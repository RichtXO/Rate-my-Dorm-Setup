from pydantic import BaseModel
from typing import List

from src.db.models import Users, Posts, Comments, Ratings
from tortoise.contrib.pydantic import pydantic_model_creator

class Follow_Pydantic(BaseModel):
    follower: str
    following: str

class FollowsOut(BaseModel):
    username: str
    follows: List[str]

class Post_Input_Pydantic(BaseModel):
    title: str
    description: str
    imagefile: str
    posted_by: str

class Comment_Input_Pydantic(BaseModel):
    postid: str
    posted_by: str
    text: str

User_Pydantic = pydantic_model_creator(Users, name="User")
Post_Pydantic = pydantic_model_creator(Posts, name="Post")
Comment_Pydantic = pydantic_model_creator(Comments, name="Comment")
Rating_Pydantic = pydantic_model_creator(Ratings, name="Rating")