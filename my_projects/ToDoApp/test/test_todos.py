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
from fastapi import Depends, status
from fastapi.testclient import TestClient
from ToDoApp.main import app
# When Python reads from ToDoApp.database import Base, it pauses executing the test_*.py file, 
# jumps inside database.py, and executes all the code inside it. This is why environment variables must be loaded before importing the application modules, 
# because database.py relies on environment variables to create the database engine and session.
from ToDoApp.models import Users, ToDos
from ToDoApp.database import Base
from ToDoApp.routers.todos import get_db
from ToDoApp.routers.auth import get_current_user
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker, Session
from typing import Annotated



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
    # This runs BEFORE any tests in this file execute
    Base.metadata.create_all(bind=engine)
    yield   # This tells pytest to run the tests after the setup code above, and then run the teardown code below after all tests complete
    # This runs AFTER all tests in this file complete
    Base.metadata.drop_all(bind=engine)


def override_get_db():
  db = TestSessionLocal()
  try:
    # yield returns the database session to the caller, allowing it to be used in the request handling logic
    yield db
  finally:
    # closes db connection after the request has been delivered, even if there was an error during the request
    db.close()


def override_get_current_user():
    # create a Users object to match what the production code expects
    return Users(
        id=1, 
        username="testuser", 
        role="admin",
        is_active=True,
        email="testuser@email.com"
    )


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user


client = TestClient(app)

@pytest.fixture(scope="function", autouse=True)
def test_todo():
  db = TestSessionLocal()

  # Create and insert a valid mock user row into the Users table
  test_user = Users(
    id=1, # Explicitly assign ID 1 to satisfy the foreign key condition
    username="testuser",
    email="testuser@email.com",
    first_name="Test",
    last_name="User",
    hashed_password="mocked_hashed_password",
    role="admin",
    is_active=True
  )
  db.add(test_user)
  db.commit()
  db.refresh(test_user)
  
  # Create and insert the todo item linked to owner_id=1
  test_todo = ToDos(
    id=1,
    title="Test ToDo",
    description="This is a test ToDo item.",
    priority=5,
    complete=False,
    owner_id=1
  )
  db.add(test_todo)
  db.commit()
  db.refresh(test_todo)

  yield test_todo    # make it available until the end of the function, then run the teardown code below
  
  # Teardown code to clean up the test data after the test runs
  # Clean up BOTH tables in the correct order (Todos first, then Users)
  db.close() # Close active session first to release any locks on the database
  with engine.connect() as connection:
    connection.execute(text("DELETE FROM todos;"))
    connection.execute(text("DELETE FROM users;"))
    connection.commit()


def test_read_all_authenticated(test_todo):
  response = client.get("/todos/")
  assert response.status_code == status.HTTP_200_OK
  assert isinstance(response.json(), list)
  assert response.json() == [{
    "id": 1,
    "title": "Test ToDo",
    "description": "This is a test ToDo item.",
    "priority": 5,
    "complete": False,
    "owner_id": 1
  }]


def test_read_one_authenticated(test_todo):
  response = client.get("/todos/todo/1")

  print(f"\n🚨 DIAGNOSTIC STATUS CODE: {response.status_code}")
  print(f"🚨 DIAGNOSTIC RESPONSE BODY: {response.json()}")

  assert response.status_code == status.HTTP_200_OK
  assert response.json() == {
    "id": 1,
    "title": "Test ToDo",
    "description": "This is a test ToDo item.",
    "priority": 5,
    "complete": False,
    "owner_id": 1
  }



# def test_create_todo_authenticated():
#     # Define the JSON body payload matching the ToDoRequest model schema
#     todo_payload = {
#         "title": "Practice testing",
#         "description": "Ensure my POST request assertions pass green",
#         "priority": 5,
#         "complete": False
#     }
    
#     # Execute the POST network call using the authenticated client
#     response = client.post("/todos/todo", json=todo_payload) 
    
#     # Assert the server returns a successful 201 Created network header package
#     assert response.status_code == status.HTTP_201_CREATED
    
#     # Verify that the saved record reflects your user authentication details
#     json_data = response.json()
#     assert json_data["title"] == todo_payload["title"]
#     assert json_data["description"] == todo_payload["description"]
#     assert json_data["owner_id"] == 1  # Confirms it securely bound to your mocked Users(id=1)
#     assert "id" in json_data           # Verifies the test database auto-assigned a primary key ID


# def test_print_all_routes():
#   # Loop through every single route registered inside your active test client app
#   for route in app.routes:
#     print(f"👉 REGISTERED PATH: {route.path}")
#   assert False # Force pytest to fail so it prints the output to your terminal screen

