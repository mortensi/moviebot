import os

from dotenv import load_dotenv

load_dotenv()

class AppConfig:
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo-0613")
    DATA_PATH = os.getenv("DATA_PATH")
    VSS_MINIMUM_SCORE = int(os.getenv("VSS_MINIMUM_SCORE", 5))
    REDIS_URL = os.getenv("REDIS_URL")
