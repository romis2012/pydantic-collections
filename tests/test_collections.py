import pytest

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


data = [
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
    user0 = User(**data[0])
    user1 = User(**data[1])

    users = UserCollection(data)
    assert len(users) == len(data)
    assert users[0] == user0
    assert users[1] == user1

    assert users.dict() == [user0.dict(), user1.dict()]

    users2 = UserCollection.parse_raw(users.json())
    for (u1, u2) in zip(users, users2):
        assert u1 == u2


def test_collection_sort():
    users = UserCollection(data)
    reversed_users = users.sort(key=lambda u: u.id, reverse=True)
    assert reversed_users[0] == users[1]
    assert reversed_users[1] == users[0]


def test_collection_assignment_validation():
    users = UserCollection()
    for item in data:
        users.append(User(**item))

    with pytest.raises(ValidationError):
        users.append(data[0])  # noqa

    with pytest.raises(ValidationError):
        users[0] = data[0]

    weak_users = WeakUserCollection()
    for d in data:
        weak_users.append(d)  # noqa

    for user in weak_users:
        assert user.__class__ is User

    for (u1, u2) in zip(weak_users, data):
        assert u1 == User(**u2)

    with pytest.raises(ValidationError):
        weak_users.append('user')  # noqa
