from __future__ import annotations
import time
from datetime import datetime, timedelta

from github.client import graphql_request
from github.queries import SEARCH_REPOS
from db.repository import upsert_repositories
from config import Config
from core.logger import get_logger

logger = get_logger()

def date_slices(start: datetime, end: datetime, step_days: int):
    cur = start
    while cur < end:
        to = min(cur + timedelta(days=step_days - 1), end)
        yield cur.date().isoformat(), to.date().isoformat()
        cur = to + timedelta(days=1)

def crawl_and_store(target_count: int, batch_size: int, days_per_slice: int) -> str:
    conn = None
    collected = 0
    batch = []
    start = datetime(2025, 1, 1)
    end = datetime.utcnow()

    try:
        from db.connection import get_db_connection
        conn = get_db_connection()

        logger.info("Applying schema if not exists")
        with conn.cursor() as cur:
            cur.execute(open("db/migrations/001_create_repositories.sql").read())
            conn.commit()

        for fr, to in date_slices(start, end, days_per_slice):
            q = f"created:{fr}..{to} stars:>0"
            logger.info(f"Crawling slice {fr} → {to}")

            cursor = None
            has = True

            while has:
                payload = {"query": SEARCH_REPOS, "variables": {"q": q, "after": cursor}}
                data = graphql_request(payload)

                search = data.get("data", {}).get("search", {})
                rate = data.get("data", {}).get("rateLimit", {})
                Config_res = Config  # alias safe reference
                logger.debug("Rate limit: %s", rate)

                # handle rate limiting
                try:
                    remaining = int(rate.get("remaining", 0))
                    if remaining < 5:
                        reset_at = rate.get("resetAt")
                        if reset_at:
                            reset_time = datetime.fromisoformat(reset_at.replace("Z", "+00:00"))
                            wait = max((reset_time - datetime.utcnow().replace(tzinfo=reset_time.tzinfo)).total_seconds(), 5)
                            logger.info(f"Rate low. Sleeping {int(wait)} seconds")
                            time.sleep(wait + 2)
                except:
                    pass

                for edge in search.get("edges", []):
                    node = edge.get("node")
                    if not node:
                        continue
                    stars = int(node.get("stargazerCount", 0))
                    batch.append((
                    node["id"],
                    node["nameWithOwner"],
                    node.get("name"),
                    node.get("owner", {}).get("login"),
                    node.get("url"),
                    stars
                ))


                    if len(batch) >= batch_size:
                        upsert_repositories(conn, batch)
                        collected += len(batch)
                        batch.clear()
                        if collected >= target_count:
                            break

                if collected >= target_count:
                    break

                pi = search.get("pageInfo", {})
                has = pi.get("hasNextPage", False)
                cursor = pi.get("endCursor")
                time.sleep(0.3)

            if collected >= target_count:
                break

        if batch:
            upsert_repositories(conn, batch)

        logger.info(f"Crawling complete total {collected}")
        return Config_res.OUT_CSV

    except Exception as e:
        logger.error("Crawler failure  %s", e)
        return Config.OUT_CSV  # safe return

    finally:
        if conn:
            conn.close()
