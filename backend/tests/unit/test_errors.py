"""Tests for custom error classes."""

import pytest
from fastapi import HTTPException

from app.utils.errors import (
    AppError,
    ConflictError,
    NotFoundError,
    RateLimitError,
    UnauthorizedError,
    UnsupportedFormatError,
    error_response,
)


class TestNotFoundError:
    def test_status_code(self):
        err = NotFoundError("Document")
        assert err.status_code == 404

    def test_message_without_id(self):
        err = NotFoundError("Document")
        assert "Document not found" in err.detail["error"]["message"]

    def test_message_with_id(self):
        err = NotFoundError("Document", "abc-123")
        assert "abc-123" in err.detail["error"]["message"]

    def test_code(self):
        err = NotFoundError("Document")
        assert err.detail["error"]["code"] == "not_found"


class TestConflictError:
    def test_status_code(self):
        err = ConflictError("Duplicate content")
        assert err.status_code == 409
        assert err.detail["error"]["code"] == "conflict"


class TestUnauthorizedError:
    def test_default_message(self):
        err = UnauthorizedError()
        assert err.status_code == 401
        assert "API key" in err.detail["error"]["message"]

    def test_custom_message(self):
        err = UnauthorizedError("Token expired")
        assert "Token expired" in err.detail["error"]["message"]


class TestRateLimitError:
    def test_status_code_and_retry(self):
        err = RateLimitError(retry_after=30)
        assert err.status_code == 429
        assert err.retry_after == 30
        assert "30s" in err.detail["error"]["message"]


class TestUnsupportedFormatError:
    def test_includes_format(self):
        err = UnsupportedFormatError(".xyz")
        assert err.status_code == 400
        assert ".xyz" in err.detail["error"]["message"]


class TestErrorResponse:
    def test_returns_json_response(self):
        resp = error_response(503, "unavailable", "Service down")
        assert resp.status_code == 503

    def test_is_http_exception_subclass(self):
        assert issubclass(AppError, HTTPException)
