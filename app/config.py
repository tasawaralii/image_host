import os
from dotenv import load_dotenv

load_dotenv()

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
DB_PATH = os.getenv("DB_PATH", "data/images.db")
API_KEY = os.getenv("API_KEY", "this_is_random_key")

RESOLUTIONS = {
    "w1280": 1280,
    "w780": 780,
    "w300": 300,
}
