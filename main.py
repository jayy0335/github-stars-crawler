from runner.crawler import crawl_and_store
from config import Config
from core.logger import get_logger

logger = get_logger()

if __name__ == "__main__":
    logger.info("Starting GitHub crawler")
    file = crawl_and_store(Config.TARGET_COUNT, Config.PAGE_BATCH, Config.DAYS_PER_SLICE)
    print("Crawl completed, CSV saved at:", file)
