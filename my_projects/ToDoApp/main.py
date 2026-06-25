import ToDoApp
from contextlib import asynccontextmanager
from pathlib import Path as FilePath
from fastapi import FastAPI, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from ToDoApp.routers import admin, auth, todos, users
from ToDoApp.models import Base
from ToDoApp.database import engine


# NOTE
# When following older FastAPI tutorials, if something inexplicable happens,check package versions. 
# FastAPI, Starlette, SQLAlchemy and Pydantic have all had breaking API changes over the last few years.




# Wrap database creation inside a clean lifespan manager (Runs ONCE when the server boots up)
@asynccontextmanager
async def lifespan(app: FastAPI):
  # A lifespan function runs whenever the FastAPI application starts.
  # i.e when you execute 'uvicorn main:app --reload' or 'pytest' command, it doesn't run when you import the app in test files
  # Create the database tables based on the models defined in models.py
  # The database schema is created when the application starts, it doesn't run if the table exists already
  Base.metadata.create_all(bind=engine)
  yield
  # Clean up actions can go here if needed


# Pass the lifespan manager into the app instantiating line, so the database tables are only created 
# when the server starts up, and not when the app is imported in test files
app = FastAPI(lifespan=lifespan)

### DELETE
# BASE_DIR = FilePath(__file__).resolve().parent
# templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app.mount("/static", StaticFiles(directory="ToDoApp/static"), name="static")

# print("LOADED MAIN FROM:", __file__)



@app.get("/healthy")
def health_check():
  return {"status": "The API is healthy!"}

# include auth.py as a route of the main app, so the endpoints defined in auth.py are available in the main app
app.include_router(admin.router)
app.include_router(users.router)
app.include_router(auth.router)
app.include_router(todos.router)

## manual version
# @app.get("/")
# def home(request: Request):
#     template = templates.get_template("home.html")
#     html = template.render(request=request)
#     return HTMLResponse(content=html)

@app.get("/")
def home(request: Request):
  return RedirectResponse(url="/todos/todo-page", status_code=status.HTTP_302_FOUND)
  # return templates.TemplateResponse(
  #   request=request,
  #   name="home.html",
  #   context={"request": request}
  # )