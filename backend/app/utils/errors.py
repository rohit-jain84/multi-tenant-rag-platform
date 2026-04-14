from fastapi import HTTPException
from fastapi.responses import JSONResponse


class AppError(HTTPException):
    def __init__(self, status_code: int, code: str, message: str):
        self.code = code
        super().__init__(status_code=status_code, detail={"error": {"code": code, "message": message}})


class NotFoundError(AppError):
    def __init__(self, resource: str, resource_id: str = ""):
        msg = f"{resource} not found" if not resource_id else f"{resource} '{resource_id}' not found"
        super().__init__(status_code=404, code="not_found", message=msg)


class ConflictError(AppError):
    def __init__(self, message: str):
        super().__init__(status_code=409, code="conflict", message=message)


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Invalid or missing API key"):
        super().__init__(status_code=401, code="unauthorized", message=message)


class RateLimitError(AppError):
    def __init__(self, retry_after: int):
        super().__init__(status_code=429, code="rate_limited", message=f"Rate limit exceeded. Retry after {retry_after}s")
        self.retry_after = retry_after


class UnsupportedFormatError(AppError):
    def __init__(self, fmt: str):
        super().__init__(status_code=400, code="unsupported_format", message=f"Unsupported document format: {fmt}")


def error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message}},
    )
