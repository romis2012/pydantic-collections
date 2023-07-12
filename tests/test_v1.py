import pytest
from pydantic_collections import PYDANTIC_V2

if PYDANTIC_V2:
    pytest.skip('Skipped', allow_module_level=True)

from typing import Optional, Union
from datetime import datetime

from pydantic import BaseModel, ValidationError
from pydantic_collections import BaseCollectionModel


class User(BaseModel):
    id: int
    name: str
    birth_date: datetime

    def __hash__(self):
        return hash((self.id, self.name, self.birth_date))

    def __eq__(self, other: 'User'):
        return (
            self.__class__ == other.__class__
            and self.id == other.id
            and self.name == other.name
            and self.birth_date == other.birth_date
        )


class UserCollection(BaseCollectionModel[User]):
    pass


class WeakUserCollection(BaseCollectionModel[User]):
    class Config:
        validate_assignment_strict = False


class OptionalIntCollection(BaseCollectionModel[Optional[int]]):
    pass


class IntOrOptionalDatetimeCollection(BaseCollectionModel[Union[int, Optional[datetime]]]):
    pass


user_data = [
    {
        'id': 1,
        'name': 'Bender',
        'birth_date': '2010-04-01T12:59:59',
    },
    {
        'id': 2,
        'name': 'Balaganov',
        'birth_date': '2020-04-01T12:59:59',
    },
]


def test_collection_validation_serialization():
    user0 = User(**user_data[0])
    user1 = User(**user_data[1])

    users = UserCollection(user_data)
    assert len(users) == len(user_data)
    assert users[0] == user0
    assert users[1] == user1

    assert users.dict() == [user0.dict(), user1.dict()]

    users2 = UserCollection.parse_raw(users.json())
    for (u1, u2) in zip(users, users2):
        assert u1 == u2

    users3 = UserCollection.parse_obj(users.dict())
    for (u1, u2) in zip(users, users3):
        assert u1 == u2


def test_collection_sort():
    users = UserCollection(user_data)
    reversed_users = users.sort(key=lambda u: u.id, reverse=True)
    assert reversed_users[0] == users[1]
    assert reversed_users[1] == users[0]


def test_collection_assignment_validation():
    users = UserCollection()
    for item in user_data:
        users.append(User(**item))

    with pytest.raises(ValidationError):
        users.append(user_data[0])  # noqa

    with pytest.raises(ValidationError):
        users[0] = user_data[0]

    weak_users = WeakUserCollection()
    for d in user_data:
        weak_users.append(d)  # noqa

    for user in weak_users:
        assert user.__class__ is User

    for (u1, u2) in zip(weak_users, user_data):
        assert u1 == User(**u2)

    with pytest.raises(ValidationError):
        weak_users.append('user')  # noqa


def test_optional_collection():
    data = [1, None]
    c = OptionalIntCollection()
    for el in data:
        c.append(el)

    for (item1, item2) in zip(c, data):
        assert item1 == item2


def test_union_collection():
    data = [1, datetime.utcnow(), None]
    c = IntOrOptionalDatetimeCollection()
    for el in data:
        c.append(el)

    for (item1, item2) in zip(c, data):
        assert item1 == item2

    with pytest.raises(ValidationError):
        c.append('data')  # noqa


def test_collection_sequence_methods():
    users = UserCollection()
    for item in user_data:
        users.append(User(**item))

    assert len(users) == len(user_data)

    user0 = User(**user_data[0])
    users.insert(0, user0)
    assert users[0] == user0
    assert len(users) == len(user_data) + 1

    users[-1] = user0
    assert users[-1] == user0

    users.clear()
    assert len(users) == 0
