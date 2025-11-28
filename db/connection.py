import psycopg2
from config import Config
from core.logger import get_logger

logger = get_logger()

def get_db_connection():
    conn = psycopg2.connect(
        host=Config.PGHOST,
        port=Config.PGPORT,
        user=Config.PGUSER,
        password=Config.PGPASSWORD,
        dbname=Config.PGDATABASE
    )
    logger.info("Connected to Postgres Database ✅")
    return conn
