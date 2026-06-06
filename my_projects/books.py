from fastapi import Body, FastAPI
from typing import Optional

app = FastAPI()

BOOKS = [
    {"title": "Title One", "author": "Author One", "category": "science"},
    {"title": "Title Two", "author": "Author Two", "category": "science"},
    {"title": "Title Three", "author": "Author Three", "category": "history"},
    {"title": "Title Four", "author": "Author Four", "category": "math"},
    {"title": "Title Five", "author": "Author Five", "category": "math"},
    {"title": "Title Six", "author": "Author Two", "category": "math"}
]

# CRUD: Create (POST), Read (GET), Update (PUT), Delete (DELETE)
# Read -> GET endpoint to return all books, a specific book by title, 
# and all books from a specific category using query parameters or path parameters

@app.get("/books")
async def read_all_books():
  return BOOKS


# ASSIGNMENT
# Create a new API Endpoint that can fetch all books from a specific author using either Path Parameters or Query Parameters.
# Route will be /books/author/{book_author}/ and the query parameter will be author={book_author}
# Define two URL paths that point to the exact same function, and provide a default value of None for the path variable 
# Route with the path parameter
@app.get("/books/byauthor/{book_author}/")
# Route with the query parameter
@app.get("/books/byauthor/")
async def read_books_by_author(book_author: Optional[str] = None, author: Optional[str] = None):
  books_to_return = []
  # determine which variable the user provided
  target_author = book_author or author
  if not target_author:
    return {"message": "Please provide an author name using either the path parameter or the query parameter"}
  
  for book in BOOKS:
    if book.get("author").casefold() == target_author.casefold():
      books_to_return.append(book)
  return books_to_return



@app.get("/books/{book_author}/")
async def read_author_category_by_query(book_author: str, category: str):
  books_to_return = []
  for book in BOOKS:
    if book.get("author").casefold() == book_author.casefold() and \
      book.get("category").casefold() == category.casefold():
      books_to_return.append(book)
  return books_to_return

# @app.get("/books/{book_title}")
# async def read_book(book_title: str):
#   for book in BOOKS:
#     if book.get("title").casefold() == book_title.casefold():
#       return book
#   return {"message": f"{book_title} not found"}

@app.get("/books/{dynamic_param}")
async def read_all_books(dynamic_param: str):
  return {"dynamic param": dynamic_param}  


# Update -> POST endpoint to create a new book and add it to the BOOKS list
# Post request methods pass information to FastAPI server using the request body 
# We need to use the Body() function from FastAPI to tell FastAPI to expect a request body in the POST request, 
# and to parse the request body as a Python dictionary that we can then use to create a new book and add it to the BOOKS list

@app.post("/books/create_book")
async def create_book(new_book=Body()):
  BOOKS.append(new_book)
  return {"message": f"Book {new_book['title']} created successfully", "book": new_book}

# Update -> PUT endpoint to update an existing book"s information by title
# We can use the same Body() function to parse the request body as a Python dictionary that
# contains the updated information for the book, and then we can find the book in the BOOKS list 
# by title and update its information with the new information from the request body

@app.put("/books/update_book")
async def update_book(book_update=Body()):
  for i in range(len(BOOKS)):
    if BOOKS[i].get("title").casefold() == book_update.get("title").casefold():
      BOOKS[i] = book_update
      return {"message": f"Book {BOOKS[i]['title']} updated successfully", "book": BOOKS[i]}
  return {"message": f"{book_update.get('title')} not found"}


# Delete -> DELETE endpoint to delete a book from the BOOKS list by title

@app.delete("/books/delete_book/{book_title}")
async def delete_book(book_title: str):
  for i in range(len(BOOKS)):
    if BOOKS[i].get("title").casefold() == book_title.casefold():
      deleted_book = BOOKS.pop(i)
      return {"message": f"Book {deleted_book['title']} deleted successfully", "book": deleted_book}
  return {"message": f"{book_title} not found"}


