from typing import List
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.db.models import Users, Posts, Comments, Ratings
from src.db.schemas import User_Pydantic, Follow_Pydantic, FollowsOut, Post_Pydantic, Post_Input_Pydantic, \
    Comment_Input_Pydantic, Comment_Pydantic, Rating_Input_Pydantic, Rating_Pydantic, \
    Post_Rating_Pydantic
from pydantic import BaseModel

from src.db.register import register_tortoise
from src.db.config import TORTOISE_ORM

from tortoise import Tortoise
from tortoise.contrib.fastapi import HTTPNotFoundError, register_tortoise
from tortoise.contrib.pydantic import pydantic_model_creator

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "https://ratemydormsetup.duckdns.org/"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app = FastAPI(title="Tortoise ORM FastAPI example")

#register_tortoise(app, config=TORTOISE_ORM, generate_schemas=False)

register_tortoise(
    app,
    db_url="sqlite://:memory:",
    modules={"models": ["src.db.models"]},
    generate_schemas=True,
    add_exception_handlers=True,
)


class Status(BaseModel):
    message: str


### USER ENDPOINTS ###
@app.post("/users", response_model=User_Pydantic)
async def create_user(user: User_Pydantic):
    user_obj = await Users.create(**user.dict(exclude_unset=True))
    return await User_Pydantic.from_tortoise_orm(user_obj)


@app.delete("/users/{user_name}", response_model=Status)
async def delete_user(user_name: str):
    deleted_count = await Users.filter(username=user_name).delete()
    if not deleted_count:
        raise HTTPException(
            status_code=404, detail=f"User {user_name} not found")
    return Status(message=f"Deleted user {user_name}")


@app.get("/users", response_model=List[User_Pydantic])
async def get_users():
    return await User_Pydantic.from_queryset(Users.all())


@app.get(
    "/users/{user_name}", response_model=User_Pydantic, responses={404: {"model": HTTPNotFoundError}}
)
async def get_user(user_name: str):
    return await User_Pydantic.from_queryset_single(Users.get(username=user_name))


### FOLLOWING ENDPOINTS ###
@app.post("/follow", response_model=Status)
async def create_follow(follow: Follow_Pydantic):
    follower_obj = await Users.get(username=follow.follower)
    following_obj = await Users.get(username=follow.following)
    if follower_obj is None or following_obj is None:
        raise HTTPException(
            status_code=404, detail=f"user 1 or 2 was not found")
    await follower_obj.follows.add(following_obj)
    return Status(message=f"User {follow.follower} followed {follow.following}")


@app.delete("/follow", response_model=Status)
async def delete_follow(follow: Follow_Pydantic):
    follower_obj = await Users.get(username=follow.follower)
    following_obj = await Users.get(username=follow.following)
    if follower_obj is None or following_obj is None:
        raise HTTPException(
            status_code=404, detail=f"user 1 or 2 was not found")
    await follower_obj.follows.remove(following_obj)
    return Status(message=f"User {follow.follower} unfollowed {follow.following}")


@app.get("/followers/{user}", response_model=FollowsOut)
async def get_followers(user: str):
    dbuser = await Users.get(username=user)
    if dbuser is None:
        raise HTTPException(status_code=404, detail=f"User {user} not found")
    results = [u.username async for u in dbuser.followers.all()]
    return FollowsOut(username=user, follows=results)


@app.get("/following/{user}", response_model=FollowsOut)
async def get_following(user: str):
    dbuser = await Users.get(username=user)
    if dbuser is None:
        raise HTTPException(status_code=404, detail=f"User {user} not found")
    results = [u.username async for u in dbuser.follows.all()]
    return FollowsOut(username=user, follows=results)


### Post Endpoints ###
@app.post('/posts', response_model=Post_Pydantic)
async def post_post(post: Post_Input_Pydantic):
    owner_obj = await Users.get(username=post.posted_by)
    if owner_obj is None:
        raise HTTPException(
            status_code=404, detail=f"User {post.owner} does not exist")
    timestamp = datetime.now()
    post_pyd = Post_Pydantic(title=post.title, description=post.description,
                             imagefile=post.imagefile, posted_at=timestamp)
    post_obj = await Posts.create(**post_pyd.dict(exclude_unset=True), posted_by=owner_obj)
    return await Post_Pydantic.from_tortoise_orm(post_obj)


@app.get('/posts', response_model=List[Post_Pydantic])
async def get_posts():
    return await Post_Pydantic.from_queryset(Posts.all())


@app.get('/posts/{user}', response_model=List[Post_Pydantic])
async def get_post_by_user(user: str):
    owner_obj = await Users.get(username=user)
    return await Post_Pydantic.from_queryset(Posts.filter(posted_by=owner_obj))


@app.delete('/posts/{id}', response_model=Status)
async def delete_post(id: str):
    deleted_count = await Posts.filter(id=id).delete()
    if not deleted_count:
        raise HTTPException(status_code=404, detail=f"Post {id} not found")
    return Status(message=f"Deleted post {id}")

### Comment Endpoints ###


@app.post('/comments', response_model=Comment_Pydantic)
async def post_comment(comment: Comment_Input_Pydantic):
    post = await Posts.get(id=comment.postid)
    owner = await Users.get(username=comment.posted_by)
    if post is None or owner is None:
        raise HTTPException(
            status_code=404, detail=f"Post {comment.postid} or user {comment.username} does not exist")

    timestamp = datetime.now()
    comm_pyd = Comment_Pydantic(text=comment.text, posted_at=timestamp)
    comm_obj = await Comments.create(**comm_pyd.dict(exclude_unset=True), posted_by=owner, post=post)
    return await Comment_Pydantic.from_tortoise_orm(comm_obj)


@app.get('/comments/{postid}', response_model=List[Comment_Pydantic])
async def get_post_comments(postid: str):
    post = await Posts.get(id=postid)
    if post is None:
        raise HTTPException(
            status_code=404, detail=f"Post {postid} does not exist")
    return await Comment_Pydantic.from_queryset(Comments.filter(post=post))


@app.delete('/comments/{id}', response_model=Status)
async def delete_comment(id: str):
    delete_count = await Comments.filter(id=id).delete()
    if not delete_count:
        raise HTTPException(status_code=404, detail=f"Comment {id} not found")
    return Status(message=f"Deleted comment {id}")

### Rating Endpoints ###


@app.post('/ratings', response_model=Rating_Pydantic)
async def post_rating(rating: Rating_Input_Pydantic):
    post = await Posts.get(id=rating.postid)
    owner = await Users.get(username=rating.rated_by)
    if post is None or owner is None:
        raise HTTPException(
            status_code=404, detail=f"User {rating.rated_by} or post {rating.postid} does not exist")
    # Check that this user has not rated this post already
    rate = await Ratings.filter(post=post, rated_by=owner)
    if len(rate) != 0:
        await Ratings.filter(id=rate[0].id).update(value=rating.value)
        rate = await Ratings.get(id=rate[0].id)
        rate_pyd = await Rating_Pydantic.from_tortoise_orm(rate)
        rate_pyd.value = rating.value
        return rate_pyd

    rate_pyd = Rating_Pydantic(value=rating.value)
    rate_obj = await Ratings.create(**rate_pyd.dict(exclude_unset=True), rated_by=owner, post=post)
    return await Rating_Pydantic.from_tortoise_orm(rate_obj)


@app.get('/ratings/{postid}/{username}', response_model=Rating_Pydantic)
async def get_rating(postid: str, username: str):
    post = await Posts.get(id=postid)
    user = await Users.get(username=username)
    if post is None:
        raise HTTPException(
            status_code=404, detail=f"Post {postid} or User {username} does not exist")
    rating = await Ratings.filter(post=post, rated_by=user)
    if len(rating) == 0:
        raise HTTPException(
            status_code=404, detail=f"User {username} has not rated post {postid}")
    return await Rating_Pydantic.from_tortoise_orm(rating[0])


@app.get('/ratings/{postid}', response_model=Post_Rating_Pydantic)
async def get_post_rating(postid: str):
    post = await Posts.get(id=postid)
    if post is None:
        raise HTTPException(
            status_code=404, detail=f"Post {postid} does not exist")
    post.posted_by = await post.posted_by
    likes = await Ratings.filter(post=post, value=True).count()
    dislikes = await Ratings.filter(post=post, value=False).count()
    rates_pyd = Post_Rating_Pydantic(postid=str(post.id), post_owner=post.posted_by.username,
                                     post_title=post.title, post_rating=likes - dislikes)
    return rates_pyd


@app.delete('/ratings/{id}', response_model=Status)
async def delete_rating(id: str):
    delete_count = await Ratings.filter(id=id).delete()
    if not delete_count:
        raise HTTPException(
            status_code=404, detail=f"Rating {id} does not exist")
    return Status(message=f"Rating {id} deleted")
