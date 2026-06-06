from fastapi import APIRouter, Depends, HTTPException, Path, status
from pydantic import BaseModel, Field
from ToDoApp.models import Users
from ToDoApp.database import SessionLocal
from sqlalchemy.orm import Session
from typing import Annotated
from passlib.context import CryptContext
from sqlite3 import IntegrityError
from starlette import status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from datetime import timedelta, datetime, timezone



router = APIRouter(
  prefix="/auth",
  tags=["auth"]
)
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")

# to get a long string for a secret key, run in terminal: $ openssl rand -hex 32
SECRET_KEY = "af128d0e764af5cbb345532ccbebb8390a1361b50af4943164350ccc9cb97fff"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30



class CreateUserRequest(BaseModel):
  username: str = Field(min_length=3)
  first_name: str = Field(min_length=1, max_length=100)
  last_name: str = Field(min_length=1, max_length=100)
  email: str = Field(min_length=3, max_length=100)
  phone_number: str = Field(default=None, max_length=20)
  password: str = Field(min_length=6)
  role: str = Field(default="user")

class Token(BaseModel):
  access_token: str
  token_type: str = "bearer"


def get_db():
  db = SessionLocal()
  try:
    # yield returns the database session to the caller, allowing it to be used in the request handling logic
    yield db
  finally:
    # closes db connection after the request has been delivered, even if there was an error during the request
    db.close()

db_dependency = Annotated[Session, Depends(get_db)]


def authenticate_user(db: db_dependency, 
                      username: Annotated[str, Path(description="The username of the user to authenticate", min_length=3)], 
                      password: Annotated[str, Path(description="The password of the user to authenticate", min_length=6)]):
  user = db.query(Users).filter(Users.username == username).first()
  if user and bcrypt_context.verify(password, user.hashed_password):
    return user
  return False


def create_access_token(username:str,
                        user_id: int,
                        role: str = "user",
                        expires_delta: timedelta = ACCESS_TOKEN_EXPIRE_MINUTES):
  to_encode = {"sub": username, "user_id": user_id, "role": role}
  # Set the expiration time for the JSON web token (jwt)
  expire = datetime.now(timezone.utc) + expires_delta
  to_encode.update({"exp": expire})
  # Encode the token using the secret key and algorithm
  return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(db: db_dependency, token: Annotated[str, Depends(oauth2_bearer)]):
  credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Authentication failed.",
    headers={"WWW-Authenticate": "Bearer"},
  )
  try:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    username: str = payload.get("sub")
    user_id: int = payload.get("user_id")
    user_role: str = payload.get("role")
    if username is None or user_id is None or user_role is None:
      raise credentials_exception
  except JWTError:
    raise credentials_exception
  user = db.query(Users).filter(Users.username == username, Users.id == user_id, Users.role == user_role).first()
  if user is None:
    raise credentials_exception
  return user


@router.post("/", status_code=status.HTTP_201_CREATED) 
async def create_user(db: db_dependency, create_user_request: CreateUserRequest):
  create_user_model = Users(
    username=create_user_request.username,
    first_name=create_user_request.first_name,
    last_name=create_user_request.last_name,
    email=create_user_request.email,
    phone_number=create_user_request.phone_number if hasattr(create_user_request, "phone_number") else None,
    hashed_password=bcrypt_context.hash(create_user_request.password),  
    role=create_user_request.role,
    is_active=True
  )
  
  try:
      db.add(create_user_model)
      db.commit()
      # When db.commit() runs, SQLAlchemy assumes the database now holds the master version of the data. 
      # By default, it clears the local memory attributes of create_user_model. 
      # When FastAPI tries to read the object right after to convert it to JSON, it sees a blank, expired container and outputs nothing.
      # FIX: Force SQLAlchemy to reload the data (including auto-generated IDs)
      db.refresh(create_user_model) 
      return create_user_model
  except IntegrityError:
      # If a duplicate username/email is caught, rollback the session and raise a clean 400
      db.rollback()
      raise HTTPException(
          status_code=status.HTTP_400_BAD_REQUEST,
          detail="Username or Email already exists."
      )


@router.post("/token", response_model=Token, status_code=status.HTTP_200_OK)
async def login_for_access_token(db: db_dependency, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
  user = authenticate_user(db, form_data.username, form_data.password)
  if not user:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Authentication failed.",
      headers={"WWW-Authenticate": "Bearer"},
    )
  
  token = create_access_token(user.username, user.id, user.role, timedelta(minutes=20))
  return {"access_token": token, "token_type": "bearer"}
  

# @router.put("/me", status_code=status.HTTP_200_OK)
# async def update_user(db: db_dependency, user: Annotated[dict, Depends(get_current_user)], create_user_request: CreateUserRequest):
#   credentials_exception = HTTPException(
#     status_code=status.HTTP_401_UNAUTHORIZED,
#     detail="Authentication failed.",
#     headers={"WWW-Authenticate": "Bearer"},
#   )
#   if user is None:
#     raise credentials_exception
  
#   user_model = db.query(Users).filter(Users.id == user.id).first()
#   if user_model is not None:
#     user_model.username = create_user_request.username
#     user_model.first_name = create_user_request.first_name
#     user_model.last_name = create_user_request.last_name
#     user_model.email = create_user_request.email
#     user_model.phone_number = create_user_request.phone_number if hasattr(create_user_request, "phone_number") else None
#     if create_user_request.password:
#       user_model.hashed_password = bcrypt_context.hash(create_user_request.password)
#     user_model.role = create_user_request.role
#     db.commit()
#     db.refresh(user_model)
#     return user_model
#   raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")