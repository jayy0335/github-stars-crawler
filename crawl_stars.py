#!/usr/bin/env python3
"""
crawl_stars.py

Fetch a target number of GitHub repositories and their star counts using the
GraphQL API, respecting rate limits & doing upserts into Postgres.

Environment variables expected:
- GITHUB_TOKEN    : GitHub token (we use the default GITHUB_TOKEN in Actions)
- PGHOST, PGPORT, PGUSER, PGPASSWORD, PGDATABASE
- TARGET_COUNT    : integer, default 100000
"""

import os
import time
import json
import math
import logging
from datetime import datetime, timedelta
import requests
import psycopg2
from psycopg2.extras import execute_values

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    raise SystemExit("GITHUB_TOKEN env var required")

PGHOST = os.getenv("PGHOST", "localhost")
PGPORT = int(os.getenv("PGPORT", "5432"))
PGUSER = os.getenv("PGUSER", "postgres")
PGPASSWORD = os.getenv("PGPASSWORD", "")
PGDATABASE = os.getenv("PGDATABASE", "postgres")

TARGET_COUNT = int(os.getenv("TARGET_COUNT", "100000"))

GRAPHQL_URL = "https://api.github.com/graphql"
HEADERS = {"Authorization": f"bearer {GITHUB_TOKEN}"}

# GraphQL fragment to fetch repo basic data
REPO_FIELDS = """
node {
  ... on Repository {
    id
    name
    nameWithOwner
    url
    stargazerCount
    createdAt
    pushedAt
    updatedAt
    owner { login }
  }
}
cursor
"""

# GraphQL search query - we'll use created: range + stars:>0 to slice results
SEARCH_QUERY = """
query($q:String!,$after:String){
  search(query: $q, type: REPOSITORY, first: 100, after: $after) {
    pageInfo { hasNextPage endCursor }
    edges {
      %s
    }
  }
  rateLimit { limit cost remaining resetAt }
}
""" % REPO_FIELDS

# Helper: perform GraphQL request with retries & exponential backoff
def graphql_request(payload, max_retries=6):
    backoff = 1.0
    for attempt in range(max_retries):
        resp = requests.post(GRAPHQL_URL, headers=HEADERS, json=payload, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            if "errors" in data:
                logging.warning("GraphQL returned errors: %s", data["errors"])
            return data
        elif resp.status_code in (502, 503, 504, 429):
            logging.warning("Transient error %s. Backing off %s sec", resp.status_code, backoff)
            time.sleep(backoff)
            backoff *= 2
            continue
        else:
            logging.error("Non-retryable HTTP error %s: %s", resp.status_code, resp.text)
            resp.raise_for_status()
    raise SystemExit("GraphQL request failed after retries")

# Respect rate limit info: sleep if remaining small
def respect_rate_limit(rate_limit):
    try:
        remaining = int(rate_limit.get("remaining", 0))
        reset_at = rate_limit.get("resetAt")
        if remaining < 10 and reset_at:
            # resetAt is in ISO8601 UTC
            reset_time = datetime.fromisoformat(reset_at.replace("Z", "+00:00"))
            wait_seconds = (reset_time - datetime.utcnow().replace(tzinfo=reset_time.tzinfo)).total_seconds()
            wait_seconds = max(wait_seconds, 5)
            logging.info("Low rate limit remaining (%s). Sleeping until reset (+%s sec)", remaining, int(wait_seconds))
            time.sleep(wait_seconds + 2)
    except Exception as e:
        logging.debug("Could not parse rate limit: %s", e)

# Simplified DB upsert batch - forces correct schema
def upsert_batch(conn, rows):
    if not rows:
        return

    with conn.cursor() as cur:
        # Ensure table exists with correct schema every time
        cur.execute("DROP TABLE IF EXISTS repositories CASCADE;")
        cur.execute("""
        CREATE TABLE repositories (
            repo_id TEXT PRIMARY KEY,
            name_with_owner TEXT NOT NULL,
            repo_name TEXT,
            owner_login TEXT,
            url TEXT,
            stars INT NOT NULL,
            last_seen TIMESTAMP WITH TIME ZONE DEFAULT now(),
            fetched_at TIMESTAMP WITH TIME ZONE DEFAULT now()
        );
        """)
        
        # Simple INSERT (no conflict handling since table is fresh)
        sql = """
        INSERT INTO repositories 
        (repo_id, name_with_owner, repo_name, owner_login, url, stars)
        VALUES %s;
        """
        execute_values(cur, sql, rows, template=None, page_size=100)
    
    conn.commit()
# Generate date ranges to slice search results to avoid the 1k search limit
def date_ranges(start_date, end_date, days_per_slice=7):
    cur = start_date
    while cur < end_date:
        end = min(cur + timedelta(days=days_per_slice - 1), end_date)
        yield cur.date().isoformat(), end.date().isoformat()
        cur = end + timedelta(days=1)

def fetch_repos_target(target_count=TARGET_COUNT):
    conn = psycopg2.connect(host=PGHOST, port=PGPORT, user=PGUSER, password=PGPASSWORD, dbname=PGDATABASE)
    logging.info("Connected to Postgres %s@%s:%s/%s", PGUSER, PGHOST, PGPORT, PGDATABASE)

    # We'll slice by creation date ranges covering recent years and go backwards - adapt if you need different slicing
    # Start from 2010-01-01 to today
    start = datetime(2010, 1, 1)
    end = datetime.utcnow()
    days_per_slice = 3  # smaller slices yield unique 100-results pages to accumulate many repos
    collected = 0
    batch = []
    BATCH_SIZE = 200

    for created_from, created_to in date_ranges(start, end, days_per_slice):
        # search query: created:YYYY-MM-DD..YYYY-MM-DD stars:>0
        q = f"created:{created_from}..{created_to} stars:>0"
        logging.info("Searching created %s .. %s", created_from, created_to)
        has_next = True
        cursor = None
        while has_next:
            variables = {"q": q, "after": cursor}
            payload = {"query": SEARCH_QUERY, "variables": variables}
            data = graphql_request(payload)
            # errors handled earlier
            search = data.get("data", {}).get("search", {})
            rate = data.get("data", {}).get("rateLimit", {})
            respect_rate_limit(rate)

            edges = search.get("edges", [])
            for e in edges:
                node = e.get("node")
                if not node:
                    continue
                repo_id = node["id"]  # always a string, keep it as TEXT
                name_with_owner = node.get("nameWithOwner")
                repo_name = node.get("name")
                owner_login = node.get("owner", {}).get("login")
                url = node.get("url")
                stars = int(node.get("stargazerCount", 0))
                if repo_id is None:
                    continue
                batch.append((repo_id, name_with_owner, repo_name, owner_login, url, stars))
                if len(batch) >= BATCH_SIZE:
                    upsert_batch(conn, batch)
                    collected += len(batch)
                    logging.info("Upserted batch. Total collected ~ %s", collected)
                    batch = []
                    if collected >= target_count:
                        logging.info("Reached target %s", target_count)
                        break
            if collected >= target_count:
                break
            pageInfo = search.get("pageInfo", {})
            has_next = pageInfo.get("hasNextPage", False)
            cursor = pageInfo.get("endCursor")
            # small throttle between pages
            time.sleep(0.5)
        if collected >= target_count:
            break

    # final flush
    if batch:
        upsert_batch(conn, batch)
        collected += len(batch)
        logging.info("Final upsert done. Total collected ~ %s", collected)

    # export to CSV (optional)
   # CSV export using PostgreSQL's copy_to method:

# export to CSV (optional)
out_file = os.getenv("OUT_CSV", "/tmp/repos_stars.csv")
with open(out_file, "w", encoding="utf-8") as f:
    with conn.cursor() as cur:
        cur.copy_to(
            f, 
            'repositories', 
            sep=',',
            null='',
            columns=('repo_id', 'name_with_owner', 'repo_name', 'owner_login', 'url', 'stars', 'fetched_at')
        )

# Add CSV header manually
import tempfile
with tempfile.NamedTemporaryFile(mode='w+', delete=False, encoding='utf-8') as temp_file:
    # Write header
    temp_file.write('repo_id,name_with_owner,repo_name,owner_login,url,stars,fetched_at\n')
    # Append the data
    with open(out_file, 'r', encoding='utf-8') as data_file:
        temp_file.write(data_file.read())

# Replace the original file
import shutil
shutil.move(temp_file.name, out_file)

logging.info("Exported CSV to %s", out_file)

if __name__ == "__main__":
    out = fetch_repos_target()
    print("CSV:", out)
