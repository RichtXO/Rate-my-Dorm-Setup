import sys, os
sys.path.insert(1, '/app')
src_dir = os.getenv('API_DIR')
if src_dir is None:
    src_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.getcwd())))
sys.path.insert(0, src_dir)

import tortoise.exceptions
from tortoise.contrib.test import finalizer, initializer

from src.db.models import Users, Posts
from src.main import app

import asyncio
from typing import Generator

import pytest
from fastapi.testclient import TestClient

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


### Test Data ###
test_user = {
    "username": "post_tester",
    "email": "post_test@email.com",
    "password": "test_password"
}

test_post = {
    "title": "Test Post Title",
    "description": "Test description.",
    "imagefile": "test/image/file/path",
    "posted_by": "post_tester"
}

test_post_fail = {
    "title": "Bad Post",
    "description": "description",
    "imagefile": "bad/image/file/path",
    "posted_by": "DoesNotExist"
}

### Helper functions ###


async def get_post_by_db(postid):
    post = await Posts.filter(id=postid)
    for p in post:
        p.posted_by = await p.posted_by
    return post


'''
Test the /posts POST method (Success)
'''


def test_create_post(client: TestClient, event_loop: asyncio.AbstractEventLoop):
    # Create the test user
    response = client.post("/users", json=test_user)
    assert response.status_code == 200, response.text

    # Attempt to create a post
    response = client.post("/posts", json=test_post)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["title"] == test_post["title"]
    assert data["description"] == test_post["description"]
    assert data["imagefile"] == test_post["imagefile"]

    # Verify database was updated properly
    post_obj = event_loop.run_until_complete(get_post_by_db(data["id"]))
    assert len(post_obj) == 1
    post_obj = post_obj[0]
    assert post_obj.title == test_post["title"]
    assert post_obj.description == test_post["description"]
    assert post_obj.imagefile == test_post["imagefile"]
    assert post_obj.posted_by.username == test_post["posted_by"]


'''
Test the /posts POST method (Failure)
'''


def test_create_post_fail(client: TestClient):
    # Attempt to create a post
    response = client.post("/posts", json=test_post_fail)
    assert response.status_code == 404


'''
Test the /posts/{user} GET method (Success)
'''


def test_get_user_posts(client: TestClient):
    # Retrieve posts under our test user
    response = client.get("/posts/" + test_user["username"])
    assert response.status_code == 200, response.text
    data = response.json()
    # Check data validity
    assert len(data) == 1
    post = data[0]
    assert post["title"] == test_post["title"]
    assert post["description"] == test_post["description"]
    assert post["imagefile"] == test_post["imagefile"]


'''
Test the /posts/{user} GET method (Failure)
'''


def test_get_user_posts_fail(client: TestClient):
    response = client.get("/posts/baduser")
    assert response.status_code == 404


'''
Test the /posts DELETE method (Success)
'''


def test_delete_post(client: TestClient, event_loop: asyncio.AbstractEventLoop):
    # Get the post id from earlier post
    response = client.get("/posts/" + test_user["username"])
    assert response.status_code == 200
    data = response.json()

    response = client.delete("/posts/" + data[0]["id"])
    assert response.status_code == 200

    # Verify database was updated properly
    post_objs = event_loop.run_until_complete(get_post_by_db(data[0]["id"]))
    assert len(post_objs) == 0


'''
Test the /posts DELETE method (Failure)
'''


def test_delete_post_fail(client: TestClient):
    response = client.delete("/posts/notapostid")
    assert response.status_code == 404
