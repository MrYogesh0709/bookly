from pydantic import BaseModel, Field
from datetime import datetime
from typing import List
from src.books.schema import Book
from src.reviews.schema import ReviewModal
import uuid


class UserCreateModel(BaseModel):
    username: str = Field(max_length=25)
    email: str = Field(max_length=40)
    password: str = Field(min_length=6)
    firstname: str = Field(max_length=25)
    lastname: str = Field(max_length=25)


class UserLoginModel(BaseModel):
    email: str = Field(max_length=40)
    password: str = Field(min_length=6)


class UserModel(BaseModel):
    uid: uuid.UUID
    username: str
    email: str
    firstname: str
    lastname: str
    is_verified: bool
    created_at: datetime
    updated_at: datetime


class UserBooksModel(UserModel):
    books: List[Book]
    reviews: List[ReviewModal]


class EmailModel(BaseModel):
    addresses: List[str]


class PasswordResetRequestModel(BaseModel):
    email: str


class PasswordResetConfirmModel(BaseModel):
    new_password: str
    confirm_password: str
