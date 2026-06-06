from typing import Optional, Annotated
from fastapi import FastAPI, Path, Query, HTTPException, Body, status
from pydantic import BaseModel, Field, model_validator
from starlette import status



app = FastAPI()


class Book:
  id: int
  title: str
  author: str
  description: str
  rating: int
  published_date: int

  def __init__(self, id, title, author, description, rating, published_date):
    self.id = id
    self.title = title
    self.author = author
    self.description = description
    self.rating = rating
    self.published_date = published_date


BOOKS = [
    Book(1, 'Computer Science Pro', 'codingwithroby', 'A very nice book!', 5, 2030),
    Book(2, 'Be Fast with FastAPI', 'codingwithroby', 'A great book!', 5, 2030),
    Book(3, 'Master Endpoints', 'codingwithroby', 'A awesome book!', 5, 2029),
    Book(4, 'HP1', 'Author 1', 'Book Description', 2, 2028),
    Book(5, 'HP2', 'Author 2', 'Book Description', 3, 2027),
    Book(6, 'HP3', 'Author 3', 'Book Description', 1, 2026)
]


class BookRequest(BaseModel):
    # 1. Default to None so Pydantic knows it is optional
    id: Optional[int] = Field(description='ID is not needed on create', default=None)
    title: str = Field(min_length=3)
    author: str = Field(min_length=2)
    description: str = Field(min_length=1, max_length=100)
    rating: int = Field(gt=0, lt=6)   # gt: greate than, lt: less than
    published_date: int = Field(gt=1999, lt=2040)

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "A new book",
                "author": "A new author",
                "description": "A new description of a book",
                "rating": 5,
                'published_date': 2000
            }
        }
    }

    # 2. This runs dynamically EVERY time a new book is created
    # The @model_validator(mode='after') decorator waits until the client sends the data, 
    # checks if an ID was provided, and runs the database logic on the fly 
    @model_validator(mode='after')
    def generate_id_if_missing(self) -> 'BookRequest':
        # capture the possibility of None or 0, since 0 is falsy in Python
        if not self.id:
            if len(BOOKS) > 0:
                # Get the ID of the last book in the list and add 1
                self.id = BOOKS[-1].id + 1
            else:
                self.id = 1
        return self




@app.get("/books", status_code=status.HTTP_200_OK)
async def read_all_books():
  return BOOKS  


@app.get("/books/{book_id}", status_code=status.HTTP_200_OK)
async def read_book_by_id(
   # Annotated binds the data type to FastAPI's specific validation metadata
    book_id: Annotated[int, Path(description="The ID of the book to fetch", gt=0)]
):
  for book in BOOKS:
    if book.id == book_id:
      return book
  raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Book with id {book_id} not found.")



# filter by rating AND/OR by published date, etc. - any attribute of the book
@app.get("/books/", status_code=status.HTTP_200_OK)
async def read_books_by(rating: Annotated[Optional[int], Query(description="The rating of the books to fetch", gt=0, lt=6)] = None,
                        published_date: Annotated[Optional[int], Query(description="The publication year of the books to fetch", gt=1999, lt=2040)] = None):
  
  if not rating and not published_date:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provide at least one query parameter: rating or published_date.")
  
  books_with_rating = []
  for book in BOOKS:
    # Both parameters are provided and BOTH must match
    if rating and published_date:
      if book.rating == rating and book.published_date == published_date:
        books_with_rating.append(book)
    # Only rating was provided, match strictly by rating
    elif rating:
      if book.rating == rating:
        books_with_rating.append(book)
    # Only published_date was provided, match strictly by published_date
    elif published_date:
      if book.published_date == published_date:
        books_with_rating.append(book)
  if len(books_with_rating) > 0:
    return books_with_rating
  raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No books with rating {rating} and published date {published_date} found.")



# @app.post("/create-book")
# async def create_book(book_request = Body()):
#   new_book = Book(id=len(BOOKS)+1, 
#                   title=book_request['title'], 
#                   author=book_request['author'], 
#                   description=book_request['description'], 
#                   rating=book_request['rating'], 
#                   published_date=book_request['published_date'])
#   BOOKS.append(new_book)
#   return new_book

@app.post("/create-book", status_code=status.HTTP_201_CREATED)
async def create_book(book_request: BookRequest):
  new_book = Book(**book_request.model_dump())  # transform the BookRequest object into a dictionary and unpack it to create a new Book object
  BOOKS.append(new_book)
  return new_book


# UPDATE
@app.put("/books/update-book", status_code=status.HTTP_204_NO_CONTENT)
async def update_book(book_request: BookRequest):
  for i in range(len(BOOKS)):
    if BOOKS[i].id == book_request.id:
      BOOKS[i] = book_request
      # confirm update
      raise HTTPException(status_code=status.HTTP_200_OK, detail=f"Updated book with id {book_request.id}.")
  raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Book with id {book_request.id} not found.")


@app.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(book_id: Annotated[int, Path(description="The ID of the book to delete", gt=0)]):
  for i in range(len(BOOKS)):
    if BOOKS[i].id == book_id:
      del BOOKS[i]
      # confirm deletion
      raise HTTPException(status_code=status.HTTP_200_OK, detail=f"Deleted book with id {book_id}.")
  raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Book with id {book_id} not found.")
