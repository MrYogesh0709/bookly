from fastapi import APIRouter, status, Depends
from fastapi.exceptions import HTTPException
from typing import List
from src.db.main import get_session
from src.books.schema import Book, BookUpdateModal, BookCreateModal, BookDetailModal
from sqlmodel.ext.asyncio.session import AsyncSession
from src.books.service import BookService
from src.auth.dependencies import AccessTokenBearer, RoleChecker
from src.errors import BookNotFound

book_router = APIRouter()
book_service = BookService()
access_token_barer = AccessTokenBearer()
role_checker = Depends(RoleChecker(["admin", "user"]))


@book_router.get("/", response_model=List[Book], dependencies=[role_checker])
async def get_all_books(
    session: AsyncSession = Depends(get_session),
    token_details: dict = Depends(access_token_barer),
) -> list:
    books = await book_service.get_all_books(session)
    return books


@book_router.get(
    "/user/{user_uid}", response_model=List[Book], dependencies=[role_checker]
)
async def get_user_books_submission(
    user_uid: str,
    session: AsyncSession = Depends(get_session),
    token_details: dict = Depends(access_token_barer),
) -> list:
    books = await book_service.get_user_books(user_uid, session)
    return books


@book_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=Book,
    dependencies=[role_checker],
)
async def create_a_book(
    book_data: BookCreateModal,
    session: AsyncSession = Depends(get_session),
    token_details: dict = Depends(access_token_barer),
) -> dict:
    user_uid = token_details.get("user")["user_uid"]
    new_book = await book_service.create_book(book_data, user_uid, session)
    return new_book


@book_router.get(
    "/{book_uid}", response_model=BookDetailModal, dependencies=[role_checker]
)
async def get_book(
    book_uid: str,
    session: AsyncSession = Depends(get_session),
    token_details: dict = Depends(access_token_barer),
) -> dict:
    book = await book_service.get_book(book_uid, session)

    if book:
        return book
    else:
        raise BookNotFound()


@book_router.patch("/{book_uid}", response_model=Book, dependencies=[role_checker])
async def update_book(
    book_uid: str,
    book_update_data: BookUpdateModal,
    session: AsyncSession = Depends(get_session),
    token_details: dict = Depends(access_token_barer),
) -> dict:
    updated_book = await book_service.update_book(book_uid, book_update_data, session)

    if updated_book is None:
        raise BookNotFound()
    else:
        return updated_book


@book_router.delete(
    "/{book_uid}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[role_checker]
)
async def delete_book(
    book_uid: str,
    session: AsyncSession = Depends(get_session),
    token_details: dict = Depends(access_token_barer),
    dependencies=[role_checker],
):
    book_to_delete = await book_service.delete_book(book_uid, session)

    if book_to_delete:
        return {"detail": "Book deleted successfully"}
    else:
        raise BookNotFound()
