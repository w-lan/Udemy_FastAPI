from fastapi import FastAPI
from ToDoApp.routers import admin, auth, todos, users
import ToDoApp.models
from ToDoApp.database import engine



app = FastAPI()

# Create the database tables based on the models defined in models.py
# The database schema is created when the application starts, it doesn't run if the table exists already
ToDoApp.models.Base.metadata.create_all(bind=engine)

@app.get("/healthy")
def health_check():
  return {"status": "The API is healthy!"}

# include auth.py as a route of the main app, so the endpoints defined in auth.py are available in the main app
app.include_router(admin.router)
app.include_router(users.router)
app.include_router(auth.router)
app.include_router(todos.router)


