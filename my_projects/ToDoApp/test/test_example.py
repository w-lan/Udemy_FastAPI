import pytest



def test_equal_or_not_equal():
  assert 1 == 1
  assert 1 != 2

def test_is_instance():
  assert isinstance(1, int)
  assert isinstance("This is a string", str)
  assert not isinstance(1, str)

def test_boolean():
  validated = True
  assert validated is True
  assert ('hello' == 'world') is False

def test_types():
  assert type(1) == int
  assert type("This is a string") == str
  assert type(1) != str
  assert type('World') is not int

  num_list = [1,2,3,4]
  any_list = [False, False]
  assert 1 in num_list
  assert 5 not in num_list
  assert all(num_list)
  assert False in any_list
  assert True not in any_list
  assert not any(any_list)

def test_greater_than_or_less_than():
  assert 5 > 3
  assert 3 < 5
  assert not (5 < 3)
  assert not (3 > 5)


class Student:
  def __init__(self, first_name: str, last_name:str, major: str, years: int):
    self.first_name = first_name
    self.last_name = last_name
    self.major = major
    self.years = years

@pytest.fixture
def default_student():
  return Student('John', 'Doe', 'Computer Science', 3)

def test_person_initialisation(default_student):
  assert default_student.first_name == 'John', 'First name should be John'
  assert default_student.last_name == 'Doe', 'Last name should be Doe'
  assert default_student.major == 'Computer Science', 'Major should be Computer Science'
  assert default_student.years == 3