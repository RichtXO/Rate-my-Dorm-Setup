from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.db.models import User_Pydantic, Users
from pydantic import BaseModel

from src.db.register import register_tortoise
from src.db.config import TORTOISE_ORM

from tortoise.contrib.fastapi import HTTPNotFoundError, register_tortoise

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

@app.get("/users", response_model=List[User_Pydantic])
async def get_users():
    return await User_Pydantic.from_queryset(Users.all())

@app.get(
    "/user/{user_name}", response_model=User_Pydantic, responses={404: {"model": HTTPNotFoundError}}
)
async def get_user(user_name: str):
    return await User_Pydantic.from_queryset_single(Users.get(username=user_name))

@app.post("/users", response_model=User_Pydantic)
async def create_user(user: User_Pydantic):
    user_obj = await Users.create(**user.dict(exclude_unset=True))
    return await User_Pydantic.from_tortoise_orm(user_obj)