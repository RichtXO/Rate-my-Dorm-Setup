import sys, os
sys.path.insert(1, '/app')
src_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.getcwd())))
sys.path.insert(0, src_dir)

import tortoise.exceptions
from tortoise.contrib.test import finalizer, initializer
from src.db.models import Users, Posts, Ratings
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

test_like = {
    # Post id needs to be retrieved at runtime
    "rated_by": "post_tester",
    "value": True
}

test_dislike = {
    # Post id needs to be retrieved at runtime
    "rated_by": "post_tester",
    "value": False
}

test_rating_fails = [
    {
        "postid": "InvalidPostID",
        "rated_by": "post_tester",
        "value": True
    },
    {
        # Get valid postid at runtime
        "rated_by": "invaliduser",
        "value": True
    }
]

### Helper functions ###


async def get_rating_by_db(postid):
    post = await Posts.get(id=postid)
    ratings = await Ratings.filter(post=post)
    for r in ratings:
        r.rated_by = await r.rated_by
        r.post = await r.post
    return ratings


'''
Test the /ratings POST method (Success)
'''


def test_create_rating(client: TestClient, event_loop: asyncio.AbstractEventLoop):
    # Create the test user and post
    response = client.post("/users", json=test_user)
    assert response.status_code == 200, response.text
    response = client.post("/posts", json=test_post)
    assert response.status_code == 200, response.text
    test_like["postid"] = response.json()["id"]
    test_dislike["postid"] = test_like["postid"]

    # Create Rating
    response = client.post("/ratings", json=test_like)
    data = response.json()
    assert data["value"] == test_like["value"]

    # Verify database was updated properly
    rating_obj = event_loop.run_until_complete(
        get_rating_by_db(test_like["postid"]))
    assert len(rating_obj) == 1
    rating_obj = rating_obj[0]
    assert rating_obj.value == test_like["value"]
    assert str(rating_obj.post.id) == test_like["postid"]
    assert rating_obj.rated_by.username == test_like["rated_by"]

    # Update the value
    response = client.post("/ratings", json=test_dislike)
    data = response.json()
    assert data["value"] == test_dislike["value"]

    # Verify database updated correctly
    rating_obj = event_loop.run_until_complete(
        get_rating_by_db(test_dislike["postid"]))
    assert len(rating_obj) == 1
    rating_obj = rating_obj[0]
    assert rating_obj.value == test_dislike["value"]
    assert str(rating_obj.post.id) == test_dislike["postid"]
    assert rating_obj.rated_by.username == test_dislike["rated_by"]


'''
Test the /ratings POST method (Failure)
'''


def test_create_rating_fail(client: TestClient):
    # Get actual postid
    test_rating_fails[1]["postid"] = test_like["postid"]
    # Attempt to create comments
    for r in test_rating_fails:
        response = client.post("/ratings", json=r)
        assert response.status_code == 404


'''
Test the /ratings/{postid} GET method
'''


def test_get_post_rating(client: TestClient):
    response = client.get("/ratings/" + test_like["postid"])
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["postid"] == test_like["postid"]
    assert data["post_owner"] == test_post["posted_by"]
    assert data["post_title"] == test_post["title"]
    assert data["post_rating"] == -1

    # Verify updating the test rating to a like again changes the overall rating
    response = client.post("/ratings", json=test_like)
    assert response.status_code == 200, response.text

    response = client.get("ratings/" + test_like["postid"])
    assert response.status_code == 200, response.text
    assert response.json()["post_rating"] == 1


'''
Test the /ratings/{postid}/{username} GET method (Success)
'''


def test_get_rating(client: TestClient):
    # Retrieve ratings under our test post
    response = client.get(
        "/ratings/" + test_like["postid"] + '/' + test_like["rated_by"])
    assert response.status_code == 200, response.text
    rating = response.json()
    # Check data validity
    assert rating["value"] == test_like["value"]


'''
Test the /ratings/{postid}/{username} GET method (Failure)
'''


def test_get_rating_fail(client: TestClient):
    # Create another user to test case where user has not rated the post
    response = client.post("/users", json={
        "username": "anotheruser",
        "email": "another@email.com",
        "password": "anotherpass"
    })
    assert response.status_code == 200

    options = ["invalidpost/" + test_like["rated_by"],
               test_like["postid"] + "/invaliduser",
               test_like["postid"] + "anotheruser"]

    for option in options:
        response = client.get("/ratings/" + option)
        assert response.status_code == 404


'''
Test the /ratings DELETE method (Success)
'''


def test_delete_ratings(client: TestClient, event_loop: asyncio.AbstractEventLoop):
    # Get the ratings id from earlier ratings
    response = client.get(
        "/ratings/" + test_like["postid"] + '/' + test_like["rated_by"])
    assert response.status_code == 200
    data = response.json()

    response = client.delete("/ratings/" + data["id"])
    assert response.status_code == 200

    # Verify database was updated properly
    rating_objs = event_loop.run_until_complete(
        get_rating_by_db(test_like["postid"]))
    assert len(rating_objs) == 0


'''
Test the /ratings DELETE method (Failure)
'''


def test_delete_rating_fail(client: TestClient):
    response = client.delete("/ratings/notaratingid")
    assert response.status_code == 404
