import sys, os
sys.path.insert(1, '/app')
src_dir = os.getenv('API_DIR')
if src_dir is None:
    src_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.getcwd())))
sys.path.insert(0, src_dir)

import tortoise.exceptions
from tortoise.contrib.test import finalizer, initializer
from src.db.models import Users
from src.main import app
import asyncio
from typing import Generator

import pytest
from fastapi.testclient import TestClient


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
user_3 = {
    "username": "test3",
    "email": "test@three.email",
    "password": "userthreepassword"
}

### Client Generators ###


@pytest.fixture(scope="module")
def client() -> Generator:
    initializer(["src.db.models"])
    with TestClient(app) as c:
        yield c
    finalizer()


@pytest.fixture(scope="module")
def event_loop(client: TestClient) -> Generator:
    yield client.task.get_loop()

### Helper functions ###


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
    user_obj = event_loop.run_until_complete(
        get_user_by_db(user_1["username"]))
    assert user_obj.username == user_1["username"]
    assert user_obj.email == user_1["email"]
    assert user_obj.password == user_1["password"]


'''
Test the /users GET method
'''


def test_get_users(client: TestClient):
    # Add second user for test case
    response = client.post("/users", json=user_2)
    assert response.status_code == 200, response.text

    # Get all users and check both users and only both users are present
    response = client.get("/users")
    assert response.status_code == 200, response.text

    data = response.json()
    assert len(data) == 2
    assert user_1 in data
    assert user_2 in data


'''
Test the /users/{username} GET method
'''


def test_get_user(client: TestClient):
    # Request the user by username
    response = client.get("/users/"+user_1["username"])
    assert response.status_code == 200, response.text

    data = response.json()
    assert data == user_1


'''
Test the /users DELETE method
'''


def test_delete_user(client: TestClient, event_loop: asyncio.AbstractEventLoop):
    # Add and delete a third user
    response = client.post("/users", json=user_3)
    assert response.status_code == 200, response.text
    response = client.delete("/users/"+user_3["username"])
    assert response.status_code == 200, response.text

    with pytest.raises(tortoise.exceptions.DoesNotExist) as exc:
        result = event_loop.run_until_complete(
            get_user_by_db(user_3["username"]))


'''
Test the /follow POST method
'''


def test_create_follow(client: TestClient, event_loop: asyncio.AbstractEventLoop):
    # Create and check follow relation
    response = client.post("/follow", json={
        "follower": user_1["username"], "following": user_2["username"]
    })
    assert response.status_code == 200, response.text

    user1_obj = event_loop.run_until_complete(
        get_user_by_db(user_1["username"]))
    user2_obj = event_loop.run_until_complete(
        get_user_by_db(user_2["username"]))

    event_loop.run_until_complete(user1_obj.fetch_related("follows"))
    event_loop.run_until_complete(user1_obj.fetch_related("followers"))
    event_loop.run_until_complete(user2_obj.fetch_related("follows"))
    event_loop.run_until_complete(user2_obj.fetch_related("followers"))
    assert len(user1_obj.follows) == 1 and len(user1_obj.followers) == 0
    assert user1_obj.follows[0] == user2_obj
    assert len(user2_obj.followers) == 1 and len(user2_obj.follows) == 0
    assert user2_obj.followers[0] == user1_obj


'''
Test the DELETE /follow method
'''


def test_delete_followers(client: TestClient, event_loop: asyncio.AbstractEventLoop):
    # Create and check new follow relation
    response = client.post("/follow", json={
        "follower": user_2["username"], "following": user_1["username"]
    })
    assert response.status_code == 200, response.text

    # Remove and verify follow relation
    response = client.delete("/follow", json={
        "follower": user_2["username"], "following": user_1["username"]
    })
    assert response.status_code == 200, response.text

    user1_obj = event_loop.run_until_complete(
        get_user_by_db(user_1["username"]))
    user2_obj = event_loop.run_until_complete(
        get_user_by_db(user_2["username"]))
    event_loop.run_until_complete(user1_obj.fetch_related("followers"))
    event_loop.run_until_complete(user2_obj.fetch_related("follows"))

    assert len(user1_obj.followers) == 0
    assert len(user2_obj.follows) == 0


'''
Test the /followers and /following GET methods
'''


def test_get_followers(client: TestClient):
    followers2 = client.get('/followers/' + user_2["username"])
    assert followers2.status_code == 200, followers2.text
    following1 = client.get('/following/' + user_1["username"])
    assert following1.status_code == 200, following1.text

    f2_data = followers2.json()
    assert f2_data["username"] == user_2["username"]
    assert len(f2_data["follows"]
               ) == 1 and f2_data["follows"][0] == user_1["username"]
    f1_data = following1.json()
    assert f1_data["username"] == user_1["username"]
    assert len(f1_data["follows"]
               ) == 1 and f1_data["follows"][0] == user_2["username"]


### ERROR CASES ###
'''
Test that POST /user throws 422 when user already exists
'''


def test_create_duplicate_user(client: TestClient):
    response = client.post("/users", json=user_1)
    assert response.status_code == 422


'''
Test that GET and DELETE /users/{username} throws a 404 when username does not exist in db
'''


def test_get_invalid_user(client: TestClient):
    for m in (client.get, client.delete):
        response = m("/users/INVALIDUSERNAME")
        assert response.status_code == 404


'''
Test that POST and DELETE /follow returns 404 when either user does not exist
'''


def test_post_invalid_follow(client: TestClient):
    for data in ({"follower": "test1", "following": "INVALID"},
                 {"follower": "INVALID", "following": "test1"}):
        for m in (client.post, client.delete):
            response = m("/follow", json=data)
            assert response.status_code == 404


'''
Test that GET /followers and GET /following return 404 when user does not exist
'''


def test_get_invalid_follow(client: TestClient):
    for endpoint in ("/followers/INVALIDUSERNAME", "/following/INVALIDUSERNAME"):
        response = client.get(endpoint)
        assert response.status_code == 404
