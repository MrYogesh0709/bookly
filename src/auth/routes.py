from fastapi import APIRouter, status, Depends, HTTPException, BackgroundTasks
from sqlmodel.ext.asyncio.session import AsyncSession
from .service import UserService
from src.db.main import get_session
from datetime import timedelta
from fastapi.responses import JSONResponse
from datetime import datetime
from .schema import (
    UserCreateModel,
    UserLoginModel,
    UserBooksModel,
    PasswordResetRequestModel,
    PasswordResetConfirmModel,
    EmailModel,
)
from .utils import (
    create_access_token,
    verify_password,
    create_url_safe_token,
    decode_url_safe_token,
    generate_password_hash,
)
from src.db.redis import add_jti_to_blocklist
from src.errors import UserAlreadyExists, UserNotFound, InvalidCredentials, InvalidToken
from .dependencies import (
    RefreshTokenBearer,
    AccessTokenBearer,
    get_current_user,
    RoleChecker,
)
from src.mail import crate_message, mail
from src.config import Config
from src.celery_tasks import send_email


auth_router = APIRouter()
user_service = UserService()
refresh_token_bearer = RefreshTokenBearer()
access_token_bearer = AccessTokenBearer()
role_checker = RoleChecker(["admin", "user"])

REFRESH_TOKEN_EXPIRY = 2


@auth_router.post("/signup", status_code=status.HTTP_201_CREATED)
async def create_user_Account(
    user_data: UserCreateModel,
    bg_task: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
):
    email = user_data.email

    user_exists = await user_service.user_exists(email, session)

    if user_exists:
        raise UserAlreadyExists()

    new_user = await user_service.create_user(user_data, session)
    token = create_url_safe_token({"email": email})

    link = f"http://{Config.DOMAIN}/api/v1/auth/verify/{token}"

    html_message = f"""
    <h1>Verify your email</h1>
    <p>Please click <a href="{link}">this link</a> to verify your email.</p>
    """
    # 1st method
    # message = crate_message(
    #     recipients=[email], subject="Verify your email", body=html_message
    # )

    # it's async but background task make it faster
    # await mail.send_message(message)
    # 2nd method

    # bg_task.add_task(mail.send_message, message)

    # 3rd best method
    emails = [email]
    send_email.delay(emails, subject="Verify your email", body=html_message)

    return {
        "message": "Account Created! Check email to verify your account",
        "User": new_user,
    }


@auth_router.get("/verify/{token}")
async def verify_token_account(
    token: str, session: AsyncSession = Depends(get_session)
):
    token_data = decode_url_safe_token(token)
    user_email = token_data.get("email")

    if user_email:
        user = await user_service.get_user_by_email(user_email, session)

        if not user:
            raise UserNotFound()

        await user_service.update_user(user, {"is_verified": True}, session=session)

        return JSONResponse(
            content={"Message": "Account is verified"}, status_code=status.HTTP_200_OK
        )

    return JSONResponse(
        content={"Message": "Error occurred during verification"},
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


@auth_router.post("/login")
async def login_users(
    login_data: UserLoginModel, session: AsyncSession = Depends(get_session)
):
    email = login_data.email
    password = login_data.password

    user = await user_service.get_user_by_email(email, session)
    if user is not None:
        password_valid = verify_password(password, user.password_hash)

        if password_valid:
            access_token = create_access_token(
                user_data={
                    "email": user.email,
                    "user_uid": str(user.uid),
                    "role": user.role,
                }
            )

            refresh_token = create_access_token(
                user_data={"email": user.email, "user_uid": str(user.uid)},
                refresh=True,
                expiry=timedelta(days=REFRESH_TOKEN_EXPIRY),
            )

            return JSONResponse(
                content={
                    "message": "Login Successful",
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "user": {"email": user.email, "uid": str(user.uid)},
                }
            )

    raise InvalidCredentials()


@auth_router.get("/refresh_token")
async def get_new_access_token(token_details: dict = Depends(refresh_token_bearer)):
    expiry_timestamp = token_details["exp"]

    if datetime.fromtimestamp(expiry_timestamp) > datetime.now():
        new_access_token = create_access_token(user_data=token_details["user"])

        return JSONResponse(content={"access_token": new_access_token})

    raise InvalidToken()


@auth_router.get("/me", response_model=UserBooksModel)
async def get_me(user=Depends(get_current_user), _: bool = Depends(role_checker)):
    return user


@auth_router.get("/logout")
async def revoke_token(token_details: dict = Depends(access_token_bearer)):
    jti = token_details["jti"]
    await add_jti_to_blocklist(jti)

    return JSONResponse(
        content={"message": "Logout successfully"}, status_code=status.HTTP_200_OK
    )


@auth_router.post("/password-reset-request")
async def password_rest_request(email_data: PasswordResetRequestModel):
    email = email_data.email

    token = create_url_safe_token({"email": email})

    link = f"http://{Config.DOMAIN}/api/v1/auth/password-rest-confirm/{token}"

    html_message = f"""
    <h1>Reset Password</h1>
    <p>Please click <a href="{link}">this link</a> reset password.</p>
    """

    message = crate_message(
        recipients=[email], subject="reset password", body=html_message
    )
    await mail.send_message(message)

    return JSONResponse(
        content={
            "message": "please check your email for reset password",
        },
        status_code=status.HTTP_200_OK,
    )


@auth_router.post("/password-rest-confirm/{token}")
async def reset_account_password(
    token: str,
    passwords: PasswordResetConfirmModel,
    session: AsyncSession = Depends(get_session),
):
    if passwords.new_password != passwords.confirm_password:
        raise HTTPException(
            detail="Password do not match", status_code=status.HTTP_400_BAD_REQUEST
        )

    token_data = decode_url_safe_token(token)
    user_email = token_data.get("email")

    if user_email:
        user = await user_service.get_user_by_email(user_email, session)

        if not user:
            raise UserNotFound()

        password_hash = generate_password_hash(passwords.new_password)

        await user_service.update_user(
            user, {"password_hash": password_hash}, session=session
        )

        return JSONResponse(
            content={"Message": "Password reset Success"},
            status_code=status.HTTP_200_OK,
        )

    return JSONResponse(
        content={"Message": "Error occurred password reset"},
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


@auth_router.post("/send-email")
async def send_email_user(emails: EmailModel):
    emails = emails.addresses
    html = "<h1>welcome</h1>"

    send_email.delay(emails, subject="hello", body=html)
