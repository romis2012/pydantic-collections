# pydantic-collections

[![CI](https://github.com/romis2012/pydantic-collections/actions/workflows/ci.yml/badge.svg)](https://github.com/romis2012/pydantic-collections/actions/workflows/ci.yml)
[![Coverage Status](https://codecov.io/gh/romis2012/pydantic-collections/branch/master/graph/badge.svg)](https://codecov.io/gh/romis2012/pydantic-collections)
[![PyPI version](https://badge.fury.io/py/pydantic-collections.svg)](https://pypi.python.org/pypi/pydantic-collections)

The `pydantic-collections` package provides `BaseCollectionModel` class that allows you 
to manipulate collections of [pydantic](https://github.com/samuelcolvin/pydantic) models 
(and any other types supported by pydantic).


## Requirements
- Python>=3.7
- pydantic>=1.8.2,<3.0


## Installation

```
pip install pydantic-collections
```

## Usage

#### Basic usage
```python

from datetime import datetime

from pydantic import BaseModel
from pydantic_collections import BaseCollectionModel


class User(BaseModel):
    id: int
    name: str
    birth_date: datetime


class UserCollection(BaseCollectionModel[User]):
    pass


 user_data = [
        {'id': 1, 'name': 'Bender', 'birth_date': '2010-04-01T12:59:59'},
        {'id': 2, 'name': 'Balaganov', 'birth_date': '2020-04-01T12:59:59'},
    ]

users = UserCollection(user_data)

print(users)
#> UserCollection([User(id=1, name='Bender', birth_date=datetime.datetime(2010, 4, 1, 12, 59, 59)), User(id=2, name='Balaganov', birth_date=datetime.datetime(2020, 4, 1, 12, 59, 59))])

print(users.dict())  # pydantic v1.x
print(users.model_dump())  # pydantic v2.x
#> [{'id': 1, 'name': 'Bender', 'birth_date': datetime.datetime(2010, 4, 1, 12, 59, 59)}, {'id': 2, 'name': 'Balaganov', 'birth_date': datetime.datetime(2020, 4, 1, 12, 59, 59)}]

print(users.json()) # pydantic v1.x
print(users.model_dump_json()) # pydantic v2.x
#> [{"id": 1, "name": "Bender", "birth_date": "2010-04-01T12:59:59"}, {"id": 2, "name": "Balaganov", "birth_date": "2020-04-01T12:59:59"}]
```

#### Strict assignment validation

By default `BaseCollectionModel` has a strict assignment check
```python
...
users = UserCollection()
users.append(User(id=1, name='Bender', birth_date=datetime.utcnow()))  # OK
users.append({'id': 1, 'name': 'Bender', 'birth_date': '2010-04-01T12:59:59'})
#> pydantic.error_wrappers.ValidationError: 1 validation error for UserCollection
#> __root__ -> 2
#>  instance of User expected (type=type_error.arbitrary_type; expected_arbitrary_type=User)
```

This behavior can be changed via Model Config

Pydantic v1.x
```python
from pydantic_collections import BaseCollectionModel
...
class UserCollection(BaseCollectionModel[User]):
    class Config:
        validate_assignment_strict = False
```

Pydantic v2.x
```python
from pydantic_collections import BaseCollectionModel, CollectionModelConfig
...
class UserCollection(BaseCollectionModel[User]):
    model_config = CollectionModelConfig(validate_assignment_strict=False)
```

```python
users = UserCollection()
users.append({'id': 1, 'name': 'Bender', 'birth_date': '2010-04-01T12:59:59'})  # OK
assert users[0].__class__ is User
assert users[0].id == 1
```

#### Using as a model field

`BaseCollectionModel` is a subclass of `BaseModel`, so you can use it as a model field
```python
...
class UserContainer(BaseModel):
    users: UserCollection = []
        
data = {
    'users': [
        {'id': 1, 'name': 'Bender', 'birth_date': '2010-04-01T12:59:59'},
        {'id': 2, 'name': 'Balaganov', 'birth_date': '2020-04-01T12:59:59'},
    ]
}

container = UserContainer(**data)
container.users.append(User(...))
...
```
