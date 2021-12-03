from tortoise import fields, models

class Users(models.Model):
    username = fields.CharField(max_length=125, unique=True, pk=True)
    email = fields.CharField(max_length=125, unique=True)
    password = fields.CharField(max_length=125, null=True)
    follows: fields.ManyToManyRelation['Users'] = fields.ManyToManyField(
        "models.Users", related_name="followers"
    )
    followers: fields.ManyToManyRelation['Users']

    def __eq__(self, user2):
        return self.username == user2.username and \
               self.email == user2.email and \
               self.password == user2.password

class Posts(models.Model):
    id = fields.UUIDField(pk=True)
    posted_by = fields.ForeignKeyField("models.Users", related_name="poster")
    title = fields.CharField(max_length=75)
    description = fields.TextField()
    imagefile = fields.TextField()
#    posted_at = fields.DatetimeField(auto_now_add=True)

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

