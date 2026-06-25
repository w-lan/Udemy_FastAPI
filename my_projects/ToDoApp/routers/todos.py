from fastapi import APIRouter, Path, Query, Depends, HTTPException, status, Request
from fastapi.templating import Jinja2Templates
from pathlib import Path as FilePath
from ToDoApp.models import ToDos, Users
from ToDoApp.database import SessionLocal
from typing import Annotated
from sqlalchemy.orm import Session
from starlette import status
from starlette.responses import RedirectResponse
from pydantic import BaseModel, Field
from .auth import get_current_user



router = APIRouter(
  prefix="/todos",
  tags=["todos"]
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


class ToDoRequest(BaseModel):
  title: str = Field(min_length=3)
  description: str = Field(min_length=1, max_length=100)
  priority: int = Field(gt=0, lt=6)  
  complete: bool = Field(default=False)


def redirect_to_login():
  redirect_response = RedirectResponse(url="/auth/login-page", status_code=status.HTTP_302_FOUND)
  redirect_response.delete_cookie(key="access_token")
  return redirect_response


BASE_DIR = FilePath(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


### PAGES ###
@router.get("/todo-page")
async def render_todo_page(request: Request, db: db_dependency):
  try:
    token = request.cookies.get('access_token')
    if token is None:
      return redirect_to_login()
    
    if token.startswith("Bearer "):
      token = token.removeprefix("Bearer ").strip()

    user = await get_current_user(db, token)
    if user is None:
      return redirect_to_login()

    todos = db.query(ToDos).filter(ToDos.owner_id == user.id).all()

    return templates.TemplateResponse(
      request=request,
      name="todo.html",
      context={"request": request,
               "todos":todos,
               "user":user
      }
    )
  except Exception as e:
    print("TODO PAGE ERROR:", repr(e))
    return redirect_to_login()


@router.get("/add-todo-page")
async def render_todo_page(request: Request, db: db_dependency):
  try:
    token = request.cookies.get('access_token')
    if token is None:
      return redirect_to_login()
    
    if token.startswith("Bearer "):
      token = token.removeprefix("Bearer ").strip()

    user = await get_current_user(db, token)
    if user is None:
      return redirect_to_login()

    return templates.TemplateResponse(
      request=request,
      name="add-todo.html",
      context={"request": request,
               "user":user
      }
    )    
  except Exception as e:
    print("TODO PAGE ERROR:", repr(e))
    return redirect_to_login()


@router.get("/edit-todo-page/{todo_id}")
async def render_edit_todo_page(request: Request, todo_id: int, db: db_dependency):
  try:
    token = request.cookies.get('access_token')
    if token is None:
      return redirect_to_login()
    
    if token.startswith("Bearer "):
      token = token.removeprefix("Bearer ").strip()

    user = await get_current_user(db, token)
    if user is None:
      return redirect_to_login()

    todo = db.query(ToDos).filter(ToDos.id == todo_id).first()

    return templates.TemplateResponse(
      request=request,
      name="edit-todo.html",
      context={"request": request,
               "todo": todo,
               "user":user
      }
    )    
  except Exception as e:
    print("TODO PAGE ERROR:", repr(e))
    return redirect_to_login()



### ENDPOINTS ###
@router.get("/", status_code=status.HTTP_200_OK)
async def read_all(db: db_dependency, user: user_dependency):
  credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Authentication failed.",
    headers={"WWW-Authenticate": "Bearer"},
  )
  if user is None:
    raise credentials_exception
  return db.query(ToDos).filter(ToDos.owner_id == user.id).all()


@router.get("/todo/{todo_id}", status_code=status.HTTP_200_OK)
async def read_todo(db: db_dependency, user: user_dependency, todo_id: Annotated[int, Path(description="The ID of the todo to read", gt=0)]):
  credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Authentication failed.",
    headers={"WWW-Authenticate": "Bearer"},
  )
  if user is None:
    raise credentials_exception
  todo_model = db.query(ToDos).filter(ToDos.id == todo_id, ToDos.owner_id == user.id).first()
  if todo_model is not None:
    return todo_model
  raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"ToDo with id {todo_id} not found.")


@router.post("/todo", status_code=status.HTTP_201_CREATED)
async def create_todo(db: db_dependency, user: user_dependency, todo_request: ToDoRequest):
  credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Authentication failed.",
    headers={"WWW-Authenticate": "Bearer"},
  )
  if user is None:
    raise credentials_exception
  # transform the ToDoRequest object into a dictionary and unpack it to create a new ToDos object, also set the owner_id to the id of the authenticated user
  todo_model = ToDos(**todo_request.model_dump(), owner_id=user.id)  
  db.add(todo_model)
  db.commit()
  db.refresh(todo_model)  # Refresh the instance to get the auto-generated ID and any other database defaults
  return todo_model


@router.put("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_todo(db: db_dependency, 
                      user: user_dependency, 
                      todo_id: Annotated[int, Path(description="The ID of the todo to update", gt=0)], 
                      todo_request: ToDoRequest):
  credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Authentication failed.",
    headers={"WWW-Authenticate": "Bearer"},
  )
  if user is None:
    raise credentials_exception  
  
  todo_model = db.query(ToDos).filter(ToDos.id == todo_id, ToDos.owner_id == user.id).first()
  if todo_model is not None:
    todo_model.title = todo_request.title
    todo_model.description = todo_request.description
    todo_model.priority = todo_request.priority
    todo_model.complete = todo_request.complete
    db.add(todo_model)
    db.commit()
    db.refresh(todo_model)
    raise HTTPException(status_code=status.HTTP_200_OK, detail=f"Updated ToDo with id {todo_id}.")
  raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"ToDo with id {todo_id} not found.")


@router.delete("/todo/{todo_id}", status_code=status.HTTP_200_OK)
async def delete_todo(db: db_dependency, 
                      user: user_dependency,
                      todo_id: Annotated[int, Path(description="The ID of the todo to delete", gt=0)]):
  credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Authentication failed.",
    headers={"WWW-Authenticate": "Bearer"},
  )
  if user is None:
    raise credentials_exception  
  todo_model = db.query(ToDos).filter(ToDos.id == todo_id, ToDos.owner_id == user.id).first()
  if todo_model is None:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"ToDo with id {todo_id} not found.")
  db.delete(todo_model)
  db.commit()
  raise HTTPException(status_code=status.HTTP_200_OK, detail=f"Deleted ToDo with id {todo_id}.")
