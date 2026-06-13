from contextlib import asynccontextmanager
from fastapi import FastAPI
import ToDoApp
from ToDoApp.routers import admin, auth, todos, users
from ToDoApp.models import Base
from ToDoApp.database import engine



# Wrap database creation inside a clean lifespan manager (Runs ONCE when the server boots up)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # This runs ONLY when you execute 'uvicorn main:app --reload' or 'pytest' command, it doesn't run when you import the app in test files
    # Create the database tables based on the models defined in models.py
    # The database schema is created when the application starts, it doesn't run if the table exists already
    Base.metadata.create_all(bind=engine)
    yield
    # Clean up actions can go here if needed


# Pass the lifespan manager into the app instantiating line, so the database tables are only created 
# when the server starts up, and not when the app is imported in test files
app = FastAPI(lifespan=lifespan)


@app.get("/healthy")
def health_check():
  return {"status": "The API is healthy!"}

# include auth.py as a route of the main app, so the endpoints defined in auth.py are available in the main app
app.include_router(admin.router)
app.include_router(users.router)
app.include_router(auth.router)
app.include_router(todos.router)


