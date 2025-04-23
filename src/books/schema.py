from pydantic import BaseModel
from datetime import datetime, date
from typing import List, Optional
from src.reviews.schema import ReviewModal
from src.tags.schemas import TagModel
import uuid


class Book(BaseModel):
    uid: uuid.UUID
    title: str
    author: str
    publisher: str
    published_date: date
    page_count: int
    language: str
    created_at: datetime
    updated_at: datetime
    tags: List[TagModel] = []


class BookDetailModal(Book):
    reviews: List[ReviewModal]
    tags: List[TagModel]


class BookCreateModal(BaseModel):
    title: str
    author: str
    publisher: str
    page_count: int
    language: str
    published_date: date


class BookUpdateModal(BaseModel):
    title: str
    author: str
    publisher: str
    page_count: int
    language: str
