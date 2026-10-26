import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./picadito.db")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8080"))
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
SITE_URL = os.getenv("SITE_URL", "http://localhost:8080")
USE_FIREBASE = os.getenv("USE_FIREBASE", "false").lower() == "true"
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "")
