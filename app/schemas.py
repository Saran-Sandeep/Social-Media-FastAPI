from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class InputPost(BaseModel):
    title: str
    content: str
    published: Optional[bool]


class Post(InputPost):
    id: int
    created_at: datetime
    modified_at: datetime

    class Config:
        from_attributes = True


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
