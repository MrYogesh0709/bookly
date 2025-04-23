from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession
from src.db.models import User
from .schema import ReviewCreateModal
from src.db.main import get_session
from .service import ReviewService
from src.errors import BookNotFound
from src.auth.dependencies import get_current_user, RoleChecker


review_router = APIRouter()
review_service = ReviewService()
admin_role_checker = Depends(RoleChecker(["admin"]))
user_role_checker = Depends(RoleChecker(["admin", "user"]))


@review_router.get("/")
async def get_all_reviews(session: AsyncSession = Depends(get_session)):
    books = await review_service.get_all_reviews(session)
    return books


@review_router.get("/{review_uid}", dependencies=[user_role_checker])
async def get_review(review_uid: str, session: AsyncSession = Depends(get_session)):
    book = await review_service.get_review(review_uid, session)

    if not book:
        raise BookNotFound()


@review_router.post("/book/{book_uid}")
async def add_review_to_book(
    book_uid: str,
    review_data: ReviewCreateModal,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    new_review = await review_service.add_review_to_book(
        user_email=current_user.email,
        book_uid=book_uid,
        review_data=review_data,
        session=session,
    )

    return new_review


@review_router.delete(
    "/{review_uid}",
    dependencies=[user_role_checker],
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_review(
    review_uid: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await review_service.delete_review_to_from_book(
        review_uid=review_uid, user_email=current_user.email, session=session
    )

    return None
