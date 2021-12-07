import os, sys
src_dir = os.getenv('API_DIR')
if src_dir is None:
    src_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.getcwd())))
sys.path.insert(0, src_dir)

from fastapi.testclient import TestClient
import pytest
from typing import Generator
import asyncio
from src.main import app
from src.db.models import Users, Posts, Comments
from tortoise.contrib.test import finalizer, initializer
import tortoise.exceptions
sys.path.insert(1, '/app')


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

test_comment = {
    # Post id needs to be retrieved before comment data can be generated
    "posted_by": "post_tester",
    "text": "I am a comment."
}

test_comment_fails = [
    {
        "postid": "IDon'tExist",
        "posted_by": "post_tester",
        "text": "I am a comment."
    },
    {
        # Want to test with a real post id, will get at runtime
        "posted_by": "doesn'texist",
        "text": "I am a comment."
    }
]

### Helper functions ###


async def get_comment_by_db(commentid):
    comment = await Comments.filter(id=commentid)
    for c in comment:
        c.posted_by = await c.posted_by
        c.post = await c.post
    return comment


'''
Test the /comments POST method (Success)
'''


def test_create_comment(client: TestClient, event_loop: asyncio.AbstractEventLoop):
    # Create the test user and post
    response = client.post("/users", json=test_user)
    assert response.status_code == 200, response.text
    response = client.post("/posts", json=test_post)
    assert response.status_code == 200, response.text
    test_comment["postid"] = response.json()["id"]

    # Create comment
    response = client.post("/comments", json=test_comment)
    data = response.json()
    assert data["text"] == test_comment["text"]

    # Verify database was updated properly
    comment_obj = event_loop.run_until_complete(get_comment_by_db(data["id"]))
    assert len(comment_obj) == 1
    comment_obj = comment_obj[0]
    assert comment_obj.text == test_comment["text"]
    assert str(comment_obj.post.id) == test_comment["postid"]
    assert comment_obj.posted_by.username == test_comment["posted_by"]


'''
Test the /comments POST method (Failure)
'''


def test_create_comment_fail(client: TestClient):
    # Get actual postid
    test_comment_fails[1]["postid"] = test_comment["postid"]
    # Attempt to create comments
    for c in test_comment_fails:
        response = client.post("/comments", json=c)
        assert response.status_code == 404


'''
Test the /comments/{postid} GET method (Success)
'''


def test_get_post_comments(client: TestClient):
    # Retrieve comments under our test post
    response = client.get("/comments/" + test_comment["postid"])
    assert response.status_code == 200, response.text
    data = response.json()
    # Check data validity
    assert len(data) == 1
    comment = data[0]
    assert comment["text"] == test_comment["text"]


'''
Test the /comments/{postid} GET method (Failure)
'''


def test_get_post_comments_fail(client: TestClient):
    response = client.get("/comments/badpost")
    assert response.status_code == 404


'''
Test the /comments DELETE method (Success)
'''


def test_delete_comment(client: TestClient, event_loop: asyncio.AbstractEventLoop):
    # Get the post id from earlier post
    response = client.get("/comments/" + test_comment["postid"])
    assert response.status_code == 200
    data = response.json()

    response = client.delete("/comments/" + data[0]["id"])
    assert response.status_code == 200

    # Verify database was updated properly
    comment_objs = event_loop.run_until_complete(
        get_comment_by_db(data[0]["id"]))
    assert len(comment_objs) == 0


'''
Test the /comments DELETE method (Failure)
'''


def test_delete_comment_fail(client: TestClient):
    response = client.delete("/comments/notacommentid")
    assert response.status_code == 404
