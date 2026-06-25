import os
import pytest
from .utils import *
from pathlib import Path
from dotenv import load_dotenv

# 1. LOAD ENVIRONMENT VARIABLES FIRST
# Load .env from project root /ToDoApp, which is one level up from the test directory
# test_todos.py is inside ToDoApp/test/, so it must step up ONE level
# parents[0] is the current /test, parents[1] is the /ToDoApp project root containing the .env file
BASE_DIR = Path(__file__).resolve().parents[1] 
load_dotenv(BASE_DIR / ".env")


# 2. THEN IMPORT THE APPLICATION MODULES
from fastapi import status
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



# imported from the router that's being tested i.e ToDoApp.routers.todos and utils.py
# override_current_user is handled in utils.py
app.dependency_overrides[get_db] = override_get_db



def test_read_all_authenticated(override_current_user, test_todo):
  response = client.get("/todos/")
  assert response.status_code == status.HTTP_200_OK
  assert isinstance(response.json(), list)
  assert response.json() == [{
    "id": test_todo.id,  # Dynamically use the ID assigned by the database during setup
    "title": "Test ToDo",
    "description": "This is a test ToDo item.",
    "priority": 5,
    "complete": False,
    "owner_id": test_todo.owner_id
  }]


def test_read_one_authenticated(override_current_user, test_todo):
  response = client.get(f"/todos/todo/{test_todo.id}")  # Dynamically use the ID assigned by the database during setup

  # print(f"\n🚨 DIAGNOSTIC STATUS CODE: {response.status_code}")
  # print(f"🚨 DIAGNOSTIC RESPONSE BODY: {response.json()}")

  assert response.status_code == status.HTTP_200_OK
  assert response.json() == {
    "id": test_todo.id,  
    "title": "Test ToDo",
    "description": "This is a test ToDo item.",
    "priority": 5,
    "complete": False,
    "owner_id": test_todo.owner_id
  }


def test_read_one_authenticated_not_found(override_current_user):
  response = client.get("/todos/todo/999")
  assert response.status_code == status.HTTP_404_NOT_FOUND
  assert response.json() == {"detail": "ToDo with id 999 not found."}


# Python creates a dependency tree, creates one User object when test_user fixture is called and passes it to override_current_user, 
# which then makes it available to all the tests that need it. 
# This way, you have a consistent test user across all tests without having to create multiple users or hardcode IDs.
def test_create_todo(test_user, override_current_user):
  # Define the JSON body payload matching the ToDoRequest model schema
  request_data = {
    "title": "Testing create todo",
    "description": "Ensure my POST request assertions pass",
    "priority": 5,
    "complete": False,
  }

  # Execute the POST network call using the authenticated client
  response = client.post("/todos/todo", json=request_data) 
  
  # To see the output printed to stdout use the -s flag when running pytest: $ pytest -s test/test_todos.py::test_create_todo
  # print(f"\n🚨 DIAGNOSTIC STATUS CODE: {response.status_code}")
  # print(f"🚨 DIAGNOSTIC RESPONSE BODY: {response.json()}")

  # Assert the server returns a successful 201 Created network header package
  assert response.status_code == status.HTTP_201_CREATED
  
  # Verify that the saved record reflects the test user authentication details
  json_data = response.json()
  assert json_data["id"] is not None        # Verifies the test database auto-assigned a primary key ID
  assert json_data["title"] == request_data["title"]
  assert json_data["description"] == request_data["description"]
  assert json_data["owner_id"] == test_user.id  # Confirms it securely bound to your mocked test_user fixture with dynamic ID assignment
    

def test_update_todo(db_session, override_current_user, test_todo):
  # Define the JSON body payload matching the ToDo already saved in the database
  request_data = {
    "title": "Change the title of the ToDo already saved",
    "description": "Ensure my POST request assertions pass",
    "priority": 5,
    "complete": False,
  }
  response = client.put(f"/todos/todo/{test_todo.id}", json=request_data)  # Dynamically use the ID assigned by the database during setup
  assert response.status_code == status.HTTP_200_OK
  
  # view stdout with $ pytest -s test/test_todos.py::test_update_todo
  # print(f"\n🚨 DIAGNOSTIC STATUS CODE: {response.status_code}")
  # print(f"🚨 DIAGNOSTIC RESPONSE BODY: {response.json()}")

  db_session.expire_all()
  
  # Dynamically use the ID assigned by the database during setup
  model = db_session.query(ToDos).filter(ToDos.id == test_todo.id).first()  
  assert model.title == request_data["title"]
  assert model.description == request_data["description"]
  assert model.owner_id == test_todo.owner_id  # Confirm the owner_id remains unchanged


def test_update_todo_not_found(db_session, override_current_user, test_todo):
  # Define the JSON body payload matching the ToDo already saved in the database
  request_data = {
    "title": "Testing ToDo not found",
    "description": "Ensure my POST request assertions pass",
    "priority": 5,
    "complete": False,
  }
  response = client.put(f"/todos/todo/999", json=request_data)  # Use a non-existent ID to trigger the 404 Not Found response
  assert response.status_code == status.HTTP_404_NOT_FOUND
  assert response.json() == {"detail": "ToDo with id 999 not found."}


def test_delete_todo(db_session, override_current_user, test_todo):
  response = client.delete(f"/todos/todo/{test_todo.id}")  # Dynamically use the ID assigned by the database during setup
  assert response.status_code == status.HTTP_200_OK
  
  model = db_session.query(ToDos).filter(ToDos.id == test_todo.id).first()  # Dynamically use the ID assigned by the database during setup
  assert model is None  # Confirm the ToDo item was deleted from the database


def test_delete_todo_not_found(db_session, override_current_user):
  response = client.delete(f"/todos/todo/999")  # Use a non-existent ID to trigger the 404 Not Found response
  assert response.status_code == status.HTTP_404_NOT_FOUND
  assert response.json() == {"detail": "ToDo with id 999 not found."}




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

