# app/schemas/service.py
"""Pydantic V2 schemas for ServiceCategory entity."""

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime


class ServiceCategoryCreate(BaseModel):
    """Admin request to create a new service category."""
    slug: str = Field(min_length=2, max_length=64)
    name: str = Field(min_length=2, max_length=120)
    description: str = Field(min_length=10, max_length=500)
    icon: Optional[str] = None
    base_price: float = Field(gt=0)
    skills: List[str] = []
    is_active: bool = True


class ServiceCategoryUpdate(BaseModel):
    """Admin request to update an existing service category (partial update)."""
    name: Optional[str] = Field(default=None, min_length=2, max_length=120)
    description: Optional[str] = Field(default=None, min_length=10, max_length=500)
    icon: Optional[str] = None
    base_price: Optional[float] = Field(default=None, gt=0)
    skills: Optional[List[str]] = None
    is_active: Optional[bool] = None


class ServiceCategoryResponse(BaseModel):
    """Service category as returned from API."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    slug: str
    name: str
    description: str
    icon: Optional[str] = None
    base_price: float
    skills: List[str] = []
    is_active: bool
    created_at: datetime


class ServiceCatalogResponse(BaseModel):
    """Paginated service catalog response."""
    items: List[ServiceCategoryResponse]
    page: int
    page_size: int
    total: int
