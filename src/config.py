import os

from dotenv import load_dotenv

load_dotenv()

class AppConfig:
    DATA_PATH = os.getenv("DATA_PATH")
    VSS_MINIMUM_SCORE = int(os.getenv("VSS_MINIMUM_SCORE", 5))
    REDIS_URL = os.getenv("REDIS_URL")
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 500))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 10))
    PAGE_TITLE = os.getenv("PAGE_TITLE", "📃 Chat Your PDF")
    PAGE_ICON = os.getenv("PAGE_ICON", "📃")
    RETRIEVE_TOP_K = int(os.getenv("RETRIEVE_TOP_K", 5))
    LLMCACHE_THRESHOLD = float(os.getenv("LLMCACHE_THRESHOLD", 0.75))
