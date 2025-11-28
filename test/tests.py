from runner.crawler import crawl_and_store
import os

os.environ["TARGET_COUNT"] = "50"

def test_sample():
    out = crawl_and_store(50, 20, 2)
    assert out is not None
