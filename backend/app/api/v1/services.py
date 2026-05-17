from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import require_role
from app.models.user import User, UserRole
from app.models.service import ServiceCategory

router = APIRouter()


class ServiceCategoryCreateRequest(BaseModel):
    slug: str = Field(min_length=2, max_length=64)
    name: str = Field(min_length=2, max_length=120)
    description: str = Field(min_length=10, max_length=500)
    icon: str | None = None
    base_price: float = Field(gt=0)
    skills: list[str] = []
    is_active: bool = True


class ServiceCategoryUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = Field(default=None, min_length=10, max_length=500)
    icon: str | None = None
    base_price: float | None = Field(default=None, gt=0)
    skills: list[str] | None = None
    is_active: bool | None = None


DEFAULT_SERVICE_CATALOG = [
    {
        "slug": "plumber",
        "name": "Plumber",
        "description": "Expert plumbing services for your home",
        "icon": "wrench",
        "base_price": 300,
        "skills": ["Pipe repair", "Fixture installation", "Leak fixing", "Drain cleaning", "Water heater"],
    },
    {
        "slug": "electrician",
        "name": "Electrician",
        "description": "Professional electrical work and repairs",
        "icon": "zap",
        "base_price": 350,
        "skills": ["Wiring", "Light installation", "Appliance repair", "Circuit breaker", "Switch repair"],
    },
    {
        "slug": "carpenter",
        "name": "Carpenter",
        "description": "Quality carpentry and furniture work",
        "icon": "hammer",
        "base_price": 400,
        "skills": ["Furniture repair", "Cabinet installation", "Door fixing", "Wood work", "Custom furniture"],
    },
    {
        "slug": "cleaner",
        "name": "Cleaner",
        "description": "Professional cleaning services",
        "icon": "sparkles",
        "base_price": 200,
        "skills": ["House cleaning", "Deep cleaning", "Bathroom cleaning", "Kitchen cleaning", "Move-in/out"],
    },
    {
        "slug": "ac-technician",
        "name": "AC Technician",
        "description": "Air conditioning repair and maintenance",
        "icon": "wind",
        "base_price": 500,
        "skills": ["AC repair", "AC installation", "Gas refilling", "Maintenance", "Duct cleaning"],
    },
    {
        "slug": "painter",
        "name": "Painter",
        "description": "Professional painting services",
        "icon": "paintbrush",
        "base_price": 350,
        "skills": ["Wall painting", "Exterior painting", "Touch-up", "Texture work", "Waterproofing"],
    },
]


def seed_default_service_categories(db: Session) -> None:
    existing = db.query(ServiceCategory).count()
    if existing > 0:
        return
    for category in DEFAULT_SERVICE_CATALOG:
        db.add(ServiceCategory(**category))
    db.commit()


@router.get("/catalog")
async def get_service_catalog(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(ServiceCategory).filter(ServiceCategory.is_active.is_(True))
    total = query.count()
    items = (
        query.order_by(ServiceCategory.name.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "items": [
            {
                "id": item.id,
                "slug": item.slug,
                "name": item.name,
                "description": item.description,
                "icon": item.icon,
                "base_price": item.base_price,
                "skills": item.skills,
            }
            for item in items
        ],
        "page": page,
        "page_size": page_size,
        "total": total,
    }


@router.get("/catalog/{service_slug}")
async def get_service_details(service_slug: str, db: Session = Depends(get_db)):
    service = db.query(ServiceCategory).filter(ServiceCategory.slug == service_slug).first()
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    return {
        "id": service.id,
        "slug": service.slug,
        "name": service.name,
        "description": service.description,
        "icon": service.icon,
        "base_price": service.base_price,
        "skills": service.skills,
        "is_active": service.is_active,
    }


@router.post("/catalog", status_code=status.HTTP_201_CREATED)
async def create_service_category(
    data: ServiceCategoryCreateRequest,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db),
):
    _ = current_user
    if db.query(ServiceCategory).filter(ServiceCategory.slug == data.slug).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Service slug already exists")
    if db.query(ServiceCategory).filter(ServiceCategory.name == data.name).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Service name already exists")

    service = ServiceCategory(**data.model_dump())
    db.add(service)
    db.commit()
    db.refresh(service)

    return {"id": service.id, "slug": service.slug, "name": service.name}


@router.patch("/catalog/{service_slug}")
async def update_service_category(
    service_slug: str,
    data: ServiceCategoryUpdateRequest,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db),
):
    _ = current_user
    service = db.query(ServiceCategory).filter(ServiceCategory.slug == service_slug).first()
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")

    updates = data.model_dump(exclude_none=True)
    for field, value in updates.items():
        setattr(service, field, value)
    db.commit()
    db.refresh(service)
    return {"id": service.id, "slug": service.slug, "name": service.name, "is_active": service.is_active}

