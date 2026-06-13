import os
from pathlib import Path
from dotenv import load_dotenv

# Let's print out what your current calculation yields
BASE_DIR = Path(__file__).resolve().parent
print(f"DEBUG: database.py is looking for .env inside: {BASE_DIR}")
print(f"DEBUG: Does .env actually exist there? {Path(BASE_DIR / '.env').exists()}")

load_dotenv(BASE_DIR / ".env")
print(f"DEBUG: Loaded DATABASE_USER: {os.getenv('DATABASE_USER')}")
