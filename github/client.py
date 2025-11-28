import requests, time
from config import Config
from core.logger import get_logger

logger = get_logger()

def graphql_request(payload, max_retries=6):
    backoff = 1.0
    for attempt in range(max_retries):
        try:
            resp = requests.post(Config.GRAPHQL_URL, headers={
                "Authorization": f"bearer {Config.GITHUB_TOKEN}"
            }, json=payload, timeout=30)
        except Exception as e:
            logger.warning("Network error, retrying: %s", e)
            time.sleep(backoff)
            backoff *= 2
            continue

        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code in (502,503,504,429):
            logger.warning("HTTP %s, backing off %s", resp.status_code, backoff)
            time.sleep(backoff)
            backoff *=2
        else:
            resp.raise_for_status()
    raise SystemExit("GitHub API failed after retries")
