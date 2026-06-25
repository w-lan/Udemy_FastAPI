from pathlib import Path
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker, DeclarativeBase


#SQLLite database
# SQL_ALCHEMY_DATABASE_URL = "sqlite:///./todosapp.db"
# engine = create_engine(SQL_ALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})   # SQLite specific argument to allow multiple threads to access the database

# Load .env from project root
BASE_DIR = Path(__file__).resolve().parent  # Go up one level to the project root
load_dotenv(BASE_DIR / ".env")

# PostgreSQL database
database_url = URL.create(
    drivername="postgresql+psycopg2",
    username=os.getenv("DATABASE_USER"),
    password=os.getenv("DATABASE_PASSWORD"),
    host=os.getenv("DATABASE_HOST"),
    database=os.getenv("DATABASE_NAME"),
)

engine = create_engine(database_url)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Modern SQLAlchemy 2.0+ approach
class Base(DeclarativeBase):
    pass