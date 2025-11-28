from __future__ import annotations
import os

class Config:
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    if not GITHUB_TOKEN:
        raise SystemExit("GITHUB_TOKEN env var required")

    PGHOST = os.getenv("PGHOST", "localhost")
    PGPORT = int(os.getenv("PGPORT", "5432"))
    PGUSER = os.getenv("PGUSER", "postgres")
    PGPASSWORD = os.getenv("PGPASSWORD", "postgres") 
    PGDATABASE = os.getenv("PGDATABASE", "postgres")

    TARGET_COUNT = int(os.getenv("TARGET_COUNT", "100000"))
    DAYS_PER_SLICE = int(os.getenv("DAYS_PER_SLICE", "3"))
    PAGE_BATCH = int(os.getenv("BATCH_SIZE", "200"))

    OUT_CSV = os.getenv("OUT_CSV", "artifacts/repos_stars.csv")

    GRAPHQL_URL = "https://api.github.com/graphql"
