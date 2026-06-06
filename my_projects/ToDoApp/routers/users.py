from fastapi import APIRouter, Body, Depends, HTTPException, Path, status
from pydantic import BaseModel, Field
from ToDoApp.models import Users
from ToDoApp.database import SessionLocal
from typing import Annotated
from sqlalchemy.orm import Session
from starlette import status
from passlib.context import CryptContext
from sqlite3 import IntegrityError
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.exc import SQLAlchemyError
from .auth import get_current_user,CreateUserRequest



router = APIRouter(
  prefix="/users",
  tags=["users"]
)
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_db():
  db = SessionLocal()
  try:
    # yield returns the database session to the caller, allowing it to be used in the request handling logic
    yield db
  finally:
    # closes db connection after the request has been delivered, even if there was an error during the request
    db.close()


# Annotated[Session, Depends(get_db)]: tells FastAPI that the db parameter should be of type Session
# Depends(get_db): handles dependency injection, telling FastAPI to use the get_db function to provide a database session for this endpoint
# Dependency Injection: a design pattern where an object receives its dependencies from an external source rather than creating them itself, 
# promoting modularity and testability
db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

# passing a Body parameter to the endpoint function, FastAPI will automatically parse the incoming JSON request body and 
# convert it into an instance of the ChangePasswordRequest model, which can then be used within the function to access the 
# data sent by the client
class ChangePasswordRequest(BaseModel):
    password: str = Field(min_length=6)
    new_password: str = Field(min_length=6)


@router.post("/", status_code=status.HTTP_200_OK) 
async def get_user(db: db_dependency, user: user_dependency):
  credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Authentication failed.",
    headers={"WWW-Authenticate": "Bearer"},
  )
  if user is None:
    raise credentials_exception  
  return db.query(Users).filter(Users.id == user.id).first()


@router.put("/change_password", status_code=status.HTTP_204_NO_CONTENT) 
async def change_password(db: db_dependency, 
                          user: user_dependency, 
                          request: ChangePasswordRequest):
  credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Authentication failed.",
    headers={"WWW-Authenticate": "Bearer"},
  )
  if user is None:
    raise credentials_exception 
 
  try:
    # Attempt to update the user's password in the database
    user_model = db.query(Users).filter(Users.id == user.id).first()
    if user_model is not None:
      # verify that the provided current password matches the stored hashed password
      if not bcrypt_context.verify(request.password, user_model.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Current password is incorrect.")
      # hash the new password and update the user's password in the database
      user_model.hashed_password = bcrypt_context.hash(request.new_password)
      db.commit()
    else:
      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
  except SQLAlchemyError as e:
    db.rollback()  # Roll back the transaction in case of an error
    # Handle the case where the new password violates a database constraint (e.g., unique constraint)
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to update password due to database integrity error.")
  

@router.put("/phone_number/{phone_number}", status_code=status.HTTP_204_NO_CONTENT) 
async def change_phone_number(db: db_dependency, 
                              user: user_dependency, 
                              phone_number: Annotated[str, Path(description="The new phone number for the user", min_length=10, max_length=15)]):
  credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Authentication failed.",
    headers={"WWW-Authenticate": "Bearer"},
  )
  if user is None:
    raise credentials_exception 

  try:
    # Attempt to update the user's phone_number in the database
    user_model = db.query(Users).filter(Users.id == user.id).first()
    if user_model is not None:
      user_model.phone_number = phone_number
      db.add(user_model)
      db.commit()
    else:
      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
  except SQLAlchemyError as e:
    db.rollback()  # Roll back the transaction in case of an error
    # Handle the case where the new phone number violates a database constraint 
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to update phone number due to database integrity error.")      