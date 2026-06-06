from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase 
from urllib.parse import quote_plus


#SQLLite database
# SQL_ALCHEMY_DATABASE_URL = "sqlite:///./todosapp.db"
# engine = create_engine(SQL_ALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})   # SQLite specific argument to allow multiple threads to access the database

# PostgreSQL database
password = quote_plus("fmM#e8%6bu65")
SQL_ALCHEMY_DATABASE_URL = f"postgresql://postgres:{password}@localhost/TodoApplicationDatabase"
engine = create_engine(SQL_ALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Modern SQLAlchemy 2.0+ approach
class Base(DeclarativeBase):
    pass