from fastapi import APIRouter, Path, Depends, HTTPException, status
from ToDoApp.models import ToDos
from ToDoApp.database import SessionLocal
from typing import Annotated
from sqlalchemy.orm import Session
from starlette import status
from .auth import get_current_user



router = APIRouter(
  prefix="/admin",
  tags=["admin"]
)


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


@router.get("/todo", status_code=status.HTTP_200_OK)
async def read_all(db: db_dependency, user: user_dependency):
  credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Authentication failed.",
    headers={"WWW-Authenticate": "Bearer"},
  )
  if user is None or user.role != "admin":
    raise credentials_exception
  return db.query(ToDos).all()


@router.delete("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(db: db_dependency, 
                      user: user_dependency,
                      todo_id: Annotated[int, Path(description="The ID of the todo to delete", gt=0)]):
  credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Authentication failed.",
    headers={"WWW-Authenticate": "Bearer"},
  )
  if user is None or user.role != "admin":
    raise credentials_exception  
  todo_model = db.query(ToDos).filter(ToDos.id == todo_id).first()
  if todo_model is not None:
    db.delete(todo_model)
    db.commit()
    raise HTTPException(status_code=status.HTTP_200_OK, detail=f"Deleted ToDo with id {todo_id}.")
  raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"ToDo with id {todo_id} not found.")