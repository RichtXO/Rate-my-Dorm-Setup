from tortoise import fields, models
from tortoise.contrib.pydantic import pydantic_model_creator

class Users(models.Model):
    username = fields.CharField(max_length=125, unique=True, pk=True)
    email = fields.CharField(max_length=125, unique=True)
    password = fields.CharField(max_length=125, null=True)

class Follows(models.Model):
    id = fields.IntField(pk=True)
    follower = fields.ForeignKeyField("models.Users", related_name="follow")
    following = fields.ForeignKeyField("models.Users", related_name="follower")

class Posts(models.Model):
    id = fields.IntField(pk=True)
    posted_by = fields.ForeignKeyField("models.Users", related_name="poster")
    title = fields.CharField(max_length=75)
    description = fields.TextField()
    posted_at = fields.DatetimeField(auto_now_add=True)

class Comments(models.Model):
    id = fields.IntField(pk=True)
    postid = fields.ForeignKeyField("models.Posts", related_name="comment")
    posted_by = fields.ForeignKeyField("models.Users", related_name="commenter")
    text = fields.TextField()
    posted_at = fields.DatetimeField(auto_now_add=True)

class Ratings(models.Model):
    id = fields.IntField(pk=True)
    rated_by = fields.ForeignKeyField("models.Users", related_name="rate")
    postid = fields.ForeignKeyField("models.Posts", related_name="ratingid")
    ratingvalue = fields.IntField()

User_Pydantic = pydantic_model_creator(Users, name="User")
Follow_Pydantic = pydantic_model_creator(Follows, name="Follow")
Post_Pydantic = pydantic_model_creator(Posts, name="Post")
Comment_Pydantic = pydantic_model_creator(Comments, name="Comment")
Rating_Pydantic = pydantic_model_creator(Ratings, name="Rating")
