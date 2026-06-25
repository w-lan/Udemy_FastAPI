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
from ToDoApp.routers.users import get_db
from ToDoApp.routers.auth import get_current_user, bcrypt_context

# imported from the router that's being tested i.e ToDoApp.routers.admin and utils.py
# override_current_user is handled in utils.py
app.dependency_overrides[get_db] = override_get_db


# Python creates a dependency tree, creates one User object when test_user fixture is called and passes it to override_current_user, 
# which then makes it available to all the tests that need it. 
# This way, you have a consistent test user across all tests without having to create multiple users or hardcode IDs.
def test_return_user(override_current_user, test_user):
  response = client.get("/users/")
  assert response.status_code == status.HTTP_200_OK
  assert response.json()["username"] == "testuser"
  assert response.json()["email"] == "testuser@email.com"
  assert response.json()["first_name"] == "Test"
  assert response.json()["last_name"] == "User"
  assert response.json()["role"] == "admin"
  assert response.json()["is_active"] == True
  assert response.json()["phone_number"] == "111 111 111"


def test_change_password_success(override_current_user, test_user):
  response = client.put("/users/change_password", json={"password": "current_password", "new_password": "new_password"})
  assert response.status_code == status.HTTP_204_NO_CONTENT


def test_change_password_invalid_current_password(override_current_user, test_user):
  response = client.put("/users/change_password", json={"password": "wrong_password", "new_password": "new_password"})
  assert response.status_code == status.HTTP_401_UNAUTHORIZED
  assert response.json() == {"detail": "Current password is incorrect."}


def test_change_phone_number_success(override_current_user, test_user):
  response = client.put("/users/phone_number/222 222 222")
  assert response.status_code == status.HTTP_204_NO_CONTENT