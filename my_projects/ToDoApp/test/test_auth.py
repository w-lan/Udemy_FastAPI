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
from fastapi import status, HTTPException
from ToDoApp.main import app
# When Python reads from ToDoApp.database import Base, it pauses executing the test_*.py file, 
# jumps inside database.py, and executes all the code inside it. This is why environment variables must be loaded before importing the application modules, 
# because database.py relies on environment variables to create the database engine and session.
from ToDoApp.models import Users, ToDos
from ToDoApp.database import Base
from ToDoApp.routers.auth import get_db, db_dependency, authenticate_user, create_access_token, SECRET_KEY, ALGORITHM, get_current_user
from jose import jwt
from datetime import timedelta, datetime, timezone



# imported from the router that's being tested i.e ToDoApp.routers.auth and utils.py
# override_current_user is handled in utils.py
app.dependency_overrides[get_db] = override_get_db


def test_authenticate_user(db_session, test_user):
  authenticated_user = authenticate_user(db_session, test_user.username, "current_password")
  assert authenticated_user is not None
  assert authenticated_user.username == test_user.username

  non_existent_user = authenticate_user(db_session, "NonExistentUserName", "current_password")
  assert non_existent_user is False

  wrong_password_user = authenticate_user(db_session, test_user.username, "wrong_password")
  assert wrong_password_user is False


def test_create_access_token(test_user):
  expires_delta = timedelta(days=1)
  test_user.role = 'User'
  token = create_access_token(test_user.username,
                              test_user.id,
                              test_user.role,
                              expires_delta)
  decoded_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={'verify_signature': False})
  assert decoded_token['sub'] == test_user.username
  assert decoded_token['user_id'] == test_user.id
  assert decoded_token['role'] == test_user.role
  

# label the test as .asyncio, and the test function as async because get_current_user is an async function
@pytest.mark.asyncio
async def test_get_current_user_valid_token(db_session, test_user):
  to_encode = {"sub": test_user.username, "user_id": test_user.id, "role": test_user.role}
  # Set the expiration time for the JSON web token (jwt)
  expires_delta = timedelta(days=1)
  expire = datetime.now(timezone.utc) + expires_delta
  to_encode.update({"exp": expire})
  # Encode the token using the secret key and algorithm
  token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

  # Use 'await' because get_current_user is an async function
  user = await get_current_user(db_session, token=token)
  assert user is not None
  assert user.username == test_user.username
  assert user.id == test_user.id
  assert user.role == test_user.role


@pytest.mark.asyncio
async def test_get_current_user_missing_payload(db_session):
  to_encode = {"role": "user"}
  # Encode the token using the secret key and algorithm
  token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

  with pytest.raises(HTTPException) as excinfo:
    await get_current_user(db_session, token=token)

  assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED
  assert excinfo.value.detail == 'Authentication failed.'
