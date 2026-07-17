import logging
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("repolens.exceptions")

class RepoLensException(Exception):
    """Base exception for all RepoLens errors"""
    def __init__(self, code: str, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class AuthenticationError(RepoLensException):
    def __init__(self, message: str = "Could not validate credentials"):
        super().__init__(
            code="AUTHENTICATION_FAILED",
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class PermissionDeniedError(RepoLensException):
    def __init__(self, message: str = "Permission denied"):
        super().__init__(
            code="PERMISSION_DENIED",
            message=message,
            status_code=status.HTTP_403_FORBIDDEN
        )


class NotFoundError(RepoLensException):
    def __init__(self, resource: str, message: str | None = None):
        super().__init__(
            code=f"{resource.upper()}_NOT_FOUND",
            message=message or f"{resource} not found.",
            status_code=status.HTTP_404_NOT_FOUND
        )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RepoLensException)
    async def repolens_exception_handler(request: Request, exc: RepoLensException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": false,
                "error": {
                    "code": exc.code,
                    "message": exc.message
                }
            }
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        # Standardise starlette/fastapi HTTPExceptions
        code = "HTTP_ERROR"
        if exc.status_code == status.HTTP_404_NOT_FOUND:
            code = "NOT_FOUND"
        elif exc.status_code == status.HTTP_401_UNAUTHORIZED:
            code = "UNAUTHORIZED"
        elif exc.status_code == status.HTTP_403_FORBIDDEN:
            code = "FORBIDDEN"
            
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": false,
                "error": {
                    "code": code,
                    "message": exc.detail
                }
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        # Custom message formatting for schema validation errors
        errors = []
        for err in exc.errors():
            loc = " -> ".join(str(x) for x in err["loc"])
            errors.append(f"{loc}: {err['msg']}")
        
        message = "Validation failed: " + "; ".join(errors)
        logger.warning(f"Validation error on {request.url.path}: {message}")
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": false,
                "error": {
                    "code": "VALIDATION_FAILED",
                    "message": message
                }
            }
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        # Catch unexpected server failures
        logger.error(f"Unhandled exception occurred: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": false,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred on the server."
                }
            }
        )
