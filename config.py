from __future__ import annotations
import os

class Config:
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    if not GITHUB_TOKEN:
        raise SystemExit("GITHUB_TOKEN env var required")

    PGHOST = os.getenv("PGHOST")
    PGPORT = int(os.getenv("PGPORT"))
    PGUSER = os.getenv("PGUSER")
    PGPASSWORD = os.getenv("PGPASSWORD") 
    PGDATABASE = os.getenv("PGDATABASE")

    TARGET_COUNT = int(os.getenv("TARGET_COUNT"))
    DAYS_PER_SLICE = int(os.getenv("DAYS_PER_SLICE"))
    PAGE_BATCH = int(os.getenv("BATCH_SIZE"))

    OUT_CSV = os.getenv("OUT_CSV")

    GRAPHQL_URL = "https://api.github.com/graphql"
