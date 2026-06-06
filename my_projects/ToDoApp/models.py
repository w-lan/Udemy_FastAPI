from ToDoApp.database import Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey


class Users(Base):
  __tablename__ = "users"

  id = Column(Integer, primary_key=True, index=True)
  email = Column(String, unique=True, index=True)
  username = Column(String, unique=True, index=True)
  first_name = Column(String, unique=False, index=False)
  last_name = Column(String, unique=False, index=False)
  hashed_password = Column(String, unique=False, index=False)
  is_active = Column(Boolean, default=True)
  role = Column(String, default="user")
  phone_number = Column(String)


class ToDos(Base):
  __tablename__ = "todos"

  id = Column(Integer, primary_key=True, index=True)
  title = Column(String)
  description = Column(String)
  priority = Column(Integer)
  complete = Column(Boolean, default=False)
  owner_id = Column(Integer, ForeignKey("users.id"))