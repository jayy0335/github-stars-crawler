from psycopg2.extras import execute_values
from core.logger import get_logger

logger = get_logger()

def upsert_repositories(conn, rows):
    """
    rows must be: (repo_id, name_with_owner, repo_name, owner_login, url, stars)
    No extra fields allowed.
    """
    if not rows:
        return

    with conn.cursor() as cur:
        sql = """
        INSERT INTO repositories (repo_id, name_with_owner, repo_name, owner_login, url, stars)
        VALUES %s
        ON CONFLICT (repo_id) DO UPDATE SET
            stars = EXCLUDED.stars,
            last_seen = now(),
            fetched_at = now()
        """
        execute_values(cur, sql, rows, page_size=100)

    conn.commit()
    logger.info("Upserted %d repos into DB ✅", len(rows))
