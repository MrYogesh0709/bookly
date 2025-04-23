from fastapi import FastAPI, status

from fastapi.requests import Request
from fastapi.responses import Response, JSONResponse
import time

from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

import logging

logger = logging.getLogger("uvicorn.access")
logger.disabled = True


def register_middleware(app: FastAPI):
    @app.middleware("http")
    async def custom_logging(request: Request, call_next):
        start_time = time.time()

        response: Response = await call_next(request)
        end_time = time.time()

        process_time = end_time - start_time

        message = f"{request.client.host}:{request.client.port} {request.method} - {request.url.path} -{response.status_code} completed after {process_time}s"

        print(message)
        return response

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

    # we have done this without middleware in auth dependency  but this one is more useful

    """
    @app.middleware("http")
    async def authorization(request: Request, call_next):
    if not "Authorization" in request.headers:
        return JSONResponse(
            content={
                "message": "Not Authenticated",
                "resolution": "Please provide the right credentials to processed",
            },
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    response = await call_next(request)
    return response
    """
