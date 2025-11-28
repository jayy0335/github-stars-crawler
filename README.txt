GitHub Stars Crawler
====================

Description
-----------
This project crawls GitHub repositories using the GraphQL API and collects star counts.
It stores the data in a PostgreSQL database and exports it to a CSV file.

The crawler respects GitHub API rate limits and retries failed requests. 
It can be run locally or automatically in GitHub Actions.

---

Folder Structure
----------------
github-stars-crawler/
├── config.py                  # Configuration for GitHub and Postgres
├── main.py                    # Entry point
├── core/
│   ├── models.py              # Data models (Repository)
│   └── logger.py              # Logger setup
├── github/
│   ├── client.py              # GraphQL request helper
│   └── queries.py             # GraphQL queries
├── db/
│   ├── connection.py          # Database connection
│   ├── repository.py          # Upsert functions
│   └── migrations/
│       └── 001_create_repositories.sql
├── runner/
│   └── crawler.py             # Main crawler logic
├── artifacts/
│   └── repos_stars.csv        # Output CSV (generated)
└── .github/workflows/
    └── crawler.yml            # GitHub Actions workflow

---

Requirements
------------
- Python 3.11+
- PostgreSQL
- pip packages:
    - requests
    - psycopg2

---

Environment Variables / Secrets
-------------------------------
Set these locally or in GitHub Actions secrets:

1. GITHUB_TOKEN     - GitHub personal access token (public repo access)
2. PGHOST           - Database host (e.g., localhost)
3. PGUSER           - Database user (e.g., postgres)
4. PGPASSWORD       - Database password (e.g., postgres)
5. PGDATABASE       - Database name (e.g., postgres)

Optional:
- TARGET_COUNT     - Number of repos to crawl (default 100000)
- DAYS_PER_SLICE   - Slice interval in days (default 3)
- BATCH_SIZE       - DB batch insert size (default 200)
- OUT_CSV          - Output CSV path (default artifacts/repos_stars.csv)

---

Running Locally
---------------
1. Set environment variables:

   Windows PowerShell:
   $env:GITHUB_TOKEN="ghp_YourTokenHere"
   $env:PGPASSWORD="ABC"
   $env:PGUSER="XYZ"
   $env:PGHOST="ABC"
   $env:PGDATABASE="ABC"

2. Install dependencies:
   pip install requests psycopg2

3. Run crawler:
   python main.py

4. CSV output will be saved at: artifacts/repos_stars.csv

---

Running in GitHub Actions
-------------------------
1. Add the environment variables as repository secrets.
2. Push the workflow file `.github/workflows/crawler.yml`.
3. Actions will automatically run the crawler daily and store CSV as an artifact.

---

Database Schema
---------------
Table: repositories

Columns:
- repo_id (TEXT PRIMARY KEY)
- name_with_owner (TEXT)
- repo_name (TEXT)
- owner_login (TEXT)
- url (TEXT)
- stars (INT)
- fetched_at (TIMESTAMPTZ, default now())
- last_seen (TIMESTAMPTZ, default now())

Indexes:
- idx_repositories_stars
- idx_repositories_owner

---

Future Improvements
-------------------
- Crawl additional metadata (issues, pull requests, comments, CI checks)
- Parallelize slices asynchronously for speed
- Persist historical star counts for analytics
- Support incremental updates to avoid full re-crawl
- Dockerize crawler for easier deployment

---

