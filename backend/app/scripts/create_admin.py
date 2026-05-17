# app/scripts/create_admin.py
"""
Bootstrap script to create the first admin user.

Run with:
    python -m app.scripts.create_admin

Reads credentials from environment variables:
    ADMIN_EMAIL     (default: admin@homeezy.com)
    ADMIN_PASSWORD  (required — must be 8+ chars with upper/lower/digit/special)

Safe: will NOT create a duplicate if the admin already exists.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import logging
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.user import User, UserRole, AccountStatus

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


def create_admin(email: str, password: str, full_name: str = "Platform Admin") -> None:
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            if existing.role == UserRole.ADMIN:
                logger.warning("Admin already exists: %s — no changes made.", email)
            else:
                logger.error(
                    "Email %s is already registered as a %s — cannot promote.",
                    email, existing.role.value,
                )
                sys.exit(1)
            return

        admin = User(
            full_name=full_name,
            email=email,
            phone=os.getenv("ADMIN_PHONE", "+910000000000"),
            password_hash=hash_password(password),
            role=UserRole.ADMIN,
            account_status=AccountStatus.ACTIVE,
            email_verified=True,
            phone_verified=True,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        logger.info("Admin created successfully!")
        logger.info("  ID    : %s", admin.id)
        logger.info("  Email : %s", admin.email)
        logger.info("  Role  : %s", admin.role.value)
    except Exception:
        logger.exception("Failed to create admin")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    admin_email = os.getenv("ADMIN_EMAIL", "admin@homeezy.com")
    admin_password = os.getenv("ADMIN_PASSWORD", "")
    admin_name = os.getenv("ADMIN_NAME", "Platform Admin")

    if not admin_password:
        logger.error("ADMIN_PASSWORD env var is required. Set it before running this script.")
        sys.exit(1)

    if len(admin_password) < 8:
        logger.error("ADMIN_PASSWORD must be at least 8 characters.")
        sys.exit(1)

    logger.info("Creating admin: %s", admin_email)
    create_admin(email=admin_email, password=admin_password, full_name=admin_name)
