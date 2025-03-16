from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class InputUser(BaseModel):
    username: str
    email: EmailStr
    password: str


class User(InputUser):
    created_at: datetime
    modified_at: datetime

    class Config:
        from_attributes = True


class UserOut(BaseModel):
    username: str
    email: EmailStr
    created_at: datetime
    modified_at: datetime

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: str


class InputPost(BaseModel):
    title: str
    content: str
    published: bool = True


class Post(InputPost):
    id: int
    created_at: datetime
    modified_at: datetime
    user_id: int
    user: UserOut

    class Config:
        from_attributes = True
