import asyncio
from typing import Generator

import pytest
from fastapi.testclient import TestClient

import sys
sys.path.insert(1, '/app')

from src.main import app
from src.db.models import Users

from tortoise.contrib.test import finalizer, initializer

### TESTING INPUT ###
user_1 = {
    "username": "test1",
    "email": "test@one.email",
    "password": "useronepassword"
}
user_2 = {
    "username": "test2",
    "email": "test@two.email",
    "password": "usertwopassword"
}
follow_1 = {
    "follower": "test1",
    "following": "test2"
}

@pytest.fixture(scope="module")
def client() -> Generator:
    initializer(["src.db.models"])
    with TestClient(app) as c:
        yield c
    finalizer()


@pytest.fixture(scope="module")
def event_loop(client: TestClient) -> Generator:
    yield client.task.get_loop()

async def get_user_by_db(uname):
    user = await Users.get(username=uname)
    return user

'''
Test the /users POST method
'''
def test_create_user(client: TestClient, event_loop: asyncio.AbstractEventLoop):
    # Check that API responds correctly to posting a new user
    response = client.post("/users", json=user_1)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data == user_1

    # Verify database was updated properly
    user_obj = event_loop.run_until_complete(get_user_by_db(user_1["username"]))
    assert user_obj.username == user_1["username"]
    assert user_obj.email == user_1["email"]
    assert user_obj.password == user_1["password"]

'''
Test the /follow POST method
'''
def test_create_follow(client: TestClient, event_loop: asyncio.AbstractEventLoop):
    # Add second user for test case
    response = client.post("/users", json=user_2)
    assert response.status_code == 200, response.text

    # Create and check follow relation
    response = client.post("/follow", json={
        "follower":user_1["username"], "following":user_2["username"]
    })
    assert response.status_code == 200, response.text

    user1_obj = event_loop.run_until_complete(get_user_by_db(user_1["username"]))
    user2_obj = event_loop.run_until_complete(get_user_by_db(user_2["username"]))

    event_loop.run_until_complete(user1_obj.fetch_related("follows"))
    event_loop.run_until_complete(user1_obj.fetch_related("followers"))
    event_loop.run_until_complete(user2_obj.fetch_related("follows"))
    event_loop.run_until_complete(user2_obj.fetch_related("followers"))
    assert len(user1_obj.follows) == 1 and len(user1_obj.followers) == 0
    assert user1_obj.follows[0] == user2_obj
    assert len(user2_obj.followers) == 1 and len(user2_obj.follows) == 0
    assert user2_obj.followers[0] == user1_obj

'''
Test the /followers and /following GET methods
'''
def test_get_followers(client: TestClient, event_loop: asyncio.AbstractEventLoop):
    followers2 = client.get('/followers/' + user_2["username"])
    assert followers2.status_code == 200, followers2.text
    following1 = client.get('/following/' + user_1["username"])
    assert following1.status_code == 200, following1.text

    f2_data = followers2.json()
    assert f2_data["username"] == user_2["username"]
    assert len(f2_data["follows"]) == 1 and f2_data["follows"][0] == user_1["username"]
    f1_data = following1.json()
    assert f1_data["username"] == user_1["username"]
    assert len(f1_data["follows"]) == 1 and f1_data["follows"][0] == user_2["username"]
