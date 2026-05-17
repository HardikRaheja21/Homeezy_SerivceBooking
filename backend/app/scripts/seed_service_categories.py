# app/scripts/seed_service_categories.py
"""
Idempotent seed script for service categories.

Run with:
    python -m app.scripts.seed_service_categories

Safe to run multiple times — skips categories that already exist.
"""

import sys
import os

# Ensure the backend root is on the path when run as __main__
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import logging
from app.core.database import SessionLocal
from app.models.service import ServiceCategory

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

SERVICE_CATALOG = [
    {
        "slug": "plumbing",
        "name": "Plumbing",
        "description": "Expert plumbing services for leaks, pipe repairs, fixtures, and water heaters.",
        "icon": "wrench",
        "base_price": 299.0,
        "skills": ["Pipe repair", "Leak fixing", "Fixture installation", "Drain cleaning", "Water heater"],
    },
    {
        "slug": "electrical",
        "name": "Electrical",
        "description": "Professional electrical work including wiring, switch repairs, and appliance installation.",
        "icon": "zap",
        "base_price": 349.0,
        "skills": ["Wiring", "Light installation", "Appliance repair", "Circuit breaker", "Switch repair"],
    },
    {
        "slug": "cleaning",
        "name": "Cleaning",
        "description": "Deep home cleaning, bathroom sanitization, kitchen cleaning, and move-in/out cleans.",
        "icon": "sparkles",
        "base_price": 199.0,
        "skills": ["Deep cleaning", "Bathroom cleaning", "Kitchen cleaning", "Sofa cleaning", "Move-out clean"],
    },
    {
        "slug": "carpentry",
        "name": "Carpentry",
        "description": "Quality carpentry for furniture assembly, door repairs, cabinet work, and custom builds.",
        "icon": "hammer",
        "base_price": 399.0,
        "skills": ["Furniture repair", "Cabinet installation", "Door fixing", "Custom furniture", "Wood polishing"],
    },
    {
        "slug": "painting",
        "name": "Painting",
        "description": "Interior and exterior painting, texture work, waterproofing, and touch-ups.",
        "icon": "paintbrush",
        "base_price": 349.0,
        "skills": ["Wall painting", "Exterior painting", "Texture work", "Waterproofing", "Touch-up"],
    },
    {
        "slug": "appliance-repair",
        "name": "Appliance Repair",
        "description": "Repair and servicing of washing machines, refrigerators, microwaves, and more.",
        "icon": "settings",
        "base_price": 299.0,
        "skills": ["Washing machine", "Refrigerator", "Microwave", "Dishwasher", "Geyser repair"],
    },
    {
        "slug": "ac-repair",
        "name": "AC Repair",
        "description": "Air conditioning repair, installation, gas refilling, and annual maintenance.",
        "icon": "wind",
        "base_price": 499.0,
        "skills": ["AC repair", "AC installation", "Gas refilling", "Annual maintenance", "Duct cleaning"],
    },
    {
        "slug": "pest-control",
        "name": "Pest Control",
        "description": "Safe and effective pest control for cockroaches, rodents, termites, and bed bugs.",
        "icon": "shield",
        "base_price": 599.0,
        "skills": ["Cockroach control", "Rodent control", "Termite treatment", "Bed bug removal", "General pest"],
    },
    {
        "slug": "salon",
        "name": "Salon at Home",
        "description": "Professional salon services at home including haircuts, facials, waxing, and grooming.",
        "icon": "scissors",
        "base_price": 249.0,
        "skills": ["Haircut", "Facial", "Waxing", "Manicure", "Pedicure", "Threading"],
    },
]


def seed(db) -> None:
    created = 0
    skipped = 0

    for item in SERVICE_CATALOG:
        exists = db.query(ServiceCategory).filter(ServiceCategory.slug == item["slug"]).first()
        if exists:
            logger.info("  SKIP  %s (already exists)", item["name"])
            skipped += 1
            continue

        category = ServiceCategory(**item)
        db.add(category)
        logger.info("  ADD   %s", item["name"])
        created += 1

    db.commit()
    logger.info("Seeding complete — %d created, %d skipped", created, skipped)


if __name__ == "__main__":
    logger.info("Starting service category seed...")
    db = SessionLocal()
    try:
        seed(db)
    except Exception:
        logger.exception("Seed failed")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()
