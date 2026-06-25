import ToDoApp.main
from ToDoApp.main import app
# print(main.__file__)
from fastapi.testclient import TestClient
from fastapi import status


client = TestClient(app)


# def test_health_check():
#   response = client.get("/healthy")
#   assert response.status_code == status.HTTP_200_OK
#   assert response.json() == {"status": "The API is healthy!"}

def test_routes():
    print(ToDoApp.main.__file__)
    print([route.path for route in app.routes])

