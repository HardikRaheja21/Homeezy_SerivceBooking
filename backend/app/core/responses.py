# app/core/responses.py
"""
Standardized API response helpers.

All Homeezy endpoints return a consistent envelope:

    { "success": true,  "message": "...", "data": {...} }
    { "success": false, "message": "...", "error": "..." }

Usage:
    from app.core.responses import ok, created, error, paginated

    return ok("Booking created", data={"booking_id": booking.id})
    return created("Worker registered", data={"user_id": user.id})
    return error("Not found", status_code=404)
"""

from fastapi.responses import JSONResponse
from typing import Any, Optional


def ok(message: str = "Success", data: Any = None) -> JSONResponse:
    """200 OK with optional data payload."""
    return JSONResponse(
        status_code=200,
        content={"success": True, "message": message, "data": data},
    )


def created(message: str = "Created", data: Any = None) -> JSONResponse:
    """201 Created with optional data payload."""
    return JSONResponse(
        status_code=201,
        content={"success": True, "message": message, "data": data},
    )


def error(message: str, status_code: int = 400, detail: Optional[str] = None) -> JSONResponse:
    """Error response — never leaks internal stack traces."""
    body: dict = {"success": False, "message": message}
    if detail:
        body["error"] = detail
    return JSONResponse(status_code=status_code, content=body)


def paginated(
    message: str,
    items: list,
    page: int,
    page_size: int,
    total: int,
) -> JSONResponse:
    """200 paginated list response."""
    total_pages = max(1, (total + page_size - 1) // page_size)
    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "message": message,
            "data": {
                "items": items,
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            },
        },
    )
