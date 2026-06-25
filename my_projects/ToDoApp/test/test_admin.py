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
from ToDoApp.main import app
# When Python reads from ToDoApp.database import Base, it pauses executing the test_*.py file, 
# jumps inside database.py, and executes all the code inside it. This is why environment variables must be loaded before importing the application modules, 
# because database.py relies on environment variables to create the database engine and session.
from ToDoApp.models import Users, ToDos
from ToDoApp.database import Base
from ToDoApp.routers.admin import get_db



# imported from the router that's being tested i.e ToDoApp.routers.admin and utils.py
# override_current_user is handled in utils.py
app.dependency_overrides[get_db] = override_get_db


def test_admin_read_all_authenticated(override_current_user, test_todo):
  response = client.get("/admin/todo")
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


def test_admin_delete_todo(db_session, override_current_user, test_todo):
  # Dynamically use the ID assigned by the database during setup
  response = client.delete(f"/todos/todo/{test_todo.id}")  
  assert response.status_code == status.HTTP_200_OK
  
  # Dynamically use the ID assigned by the database during setup
  model = db_session.query(ToDos).filter(ToDos.id == test_todo.id).first()  

  # Todo has been deleted, model should be None
  assert model is None


def test_admin_delete_todo_not_found(db_session, override_current_user):
  # Dynamically use the ID assigned by the database during setup
  response = client.delete(f"/todos/todo/9999")
  assert response.status_code == status.HTTP_404_NOT_FOUND
  assert response.json() == {"detail": "ToDo with id 9999 not found."} 