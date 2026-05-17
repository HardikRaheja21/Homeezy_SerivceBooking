# app/utils/pagination.py
"""
Reusable pagination utilities for all list endpoints.

Usage in a route:
    from app.utils.pagination import pagination_params, PaginationParams, PaginatedResponse

    @router.get("/items", response_model=PaginatedResponse[ItemSchema])
    async def list_items(pagination: PaginationParams = Depends(pagination_params), ...):
        query = db.query(Item)
        total = query.count()
        items = query.offset(pagination.offset).limit(pagination.limit).all()
        return PaginatedResponse.create(items, pagination.page, pagination.page_size, total)
"""

from pydantic import BaseModel, Field
from fastapi import Query
from typing import TypeVar, Generic, List

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Parsed pagination parameters — use via the `pagination_params` dependency."""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    @property
    def offset(self) -> int:
        """SQL OFFSET — number of rows to skip."""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """SQL LIMIT — number of rows to return."""
        return self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Generic paginated response wrapper.
    Attach to a response_model with the item type, e.g.:
        response_model=PaginatedResponse[BookingListItem]
    """
    items: List[T]
    page: int
    page_size: int
    total: int
    total_pages: int
    has_next: bool
    has_prev: bool

    @classmethod
    def create(
        cls,
        items: List[T],
        page: int,
        page_size: int,
        total: int,
    ) -> "PaginatedResponse[T]":
        total_pages = max(1, (total + page_size - 1) // page_size)
        return cls(
            items=items,
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )


def pagination_params(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page (max 100)"),
) -> PaginationParams:
    """FastAPI dependency — inject into any list endpoint as Depends(pagination_params)."""
    return PaginationParams(page=page, page_size=page_size)
