import os
import pytest
from pathlib import Path
from dotenv import load_dotenv

# 1. LOAD ENVIRONMENT VARIABLES FIRST
# Load .env from project root /ToDoApp, which is one level up from the test directory
# test_todos.py is inside ToDoApp/test/, so it must step up ONE level
# parents[0] is the current /test, parents[1] is the /ToDoApp project root containing the .env file
BASE_DIR = Path(__file__).resolve().parents[1] 
load_dotenv(BASE_DIR / ".env")


# 2. THEN IMPORT THE APPLICATION MODULES
from fastapi.testclient import TestClient
from ToDoApp.main import app
# When Python reads from ToDoApp.database import Base, it pauses executing the test_*.py file, 
# jumps inside database.py, and executes all the code inside it. This is why environment variables must be loaded before importing the application modules, 
# because database.py relies on environment variables to create the database engine and session.
from ToDoApp.models import Users, ToDos
from ToDoApp.database import Base
from ToDoApp.routers.todos import get_db
from ToDoApp.routers.auth import get_current_user, bcrypt_context
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker, Session



# PostgreSQL database
# engine = create_engine("postgresql+psycopg2://postgres:6P8FVexVA2q5@localhost:5432/TestTodoApplicationDatabase")  # ** hardcoded connection string for testing only
test_database_url = URL.create(
    drivername="postgresql+psycopg2",
    username=os.getenv("TEST_DATABASE_USER"),
    password=os.getenv("TEST_DATABASE_PASSWORD"),
    host=os.getenv("TEST_DATABASE_HOST"),
    database=os.getenv("TEST_DATABASE_NAME"),
)

engine = create_engine(test_database_url)



TestSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


@pytest.fixture(scope="module", autouse=True)
def setup_test_database():
  """
  This runs once BEFORE any tests in this file execute
  """
  Base.metadata.create_all(bind=engine)

  yield   # This tells pytest to run the tests after the setup code above

  # Teardown AFTER all tests in this file complete
  Base.metadata.drop_all(bind=engine)



@pytest.fixture(scope="function", autouse=True)
def clean_database():
  """
  This runs BEFORE and AFTER each test in this file executes, ensuring a clean slate for the next test
  """
  with engine.begin() as connection:
    connection.execute(text("TRUNCATE TABLE todos, users RESTART IDENTITY CASCADE;"))

  yield

  # engine.begin() automatically commits the transaction, so you don't need an explicit connection.commit().
  with engine.begin() as connection:
    connection.execute(text("TRUNCATE TABLE todos, users RESTART IDENTITY CASCADE;"))


# Used directly inside pytest tests/fixtures
@pytest.fixture(scope="function", autouse=True)
def db_session():
  db = TestSessionLocal()
  try:
    # yield returns the database session to the caller, allowing it to be used in the request handling logic
    yield db
  finally:
    # closes db connection after the request has been delivered, even if there was an error during the request
    db.close()


# Used by FastAPI routes during client.get/post/put/delete calls to provide a database session,
# which is overridden to use the test database session instead of the production one
def override_get_db():
  db = TestSessionLocal()
  try:
    yield db
  finally:
    db.close()


# Create a lightweight user-only fixture for creation tests
@pytest.fixture(scope="function")
def test_user(db_session):
    user = Users(
        # id=1,     # ** Let the database auto-assign the ID to avoid conflicts with multiple test runs
        username="testuser",
        email="testuser@email.com",
        first_name="Test",
        last_name="User",
        hashed_password=bcrypt_context.hash("current_password"),
        role="admin",
        is_active=True,
        phone_number="111 111 111"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    yield user  # make it available until the end of the function


@pytest.fixture(scope="function")
def override_current_user(test_user):
  def _override_get_current_user():
    return Users(
      id=test_user.id,
      username=test_user.username,
      email=test_user.email,
      role=test_user.role,
      is_active=test_user.is_active,
      phone_number=test_user.phone_number
    )

  app.dependency_overrides[get_current_user] = _override_get_current_user
  yield
  app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture(scope="function")
def test_todo(db_session, test_user):
  # Create and insert the todo item linked to owner_id=1
  test_todo = ToDos(
    # id=1,   # ** Let the database auto-assign the ID to avoid conflicts with multiple test runs
    title="Test ToDo",
    description="This is a test ToDo item.",
    priority=5,
    complete=False,
    owner_id=test_user.id  # Dynamically link to the test user fixture with dynamic ID assignment
  )
  db_session.add(test_todo)
  db_session.commit()
  db_session.refresh(test_todo)
  yield test_todo    # make it available until the end of the function


client = TestClient(app)