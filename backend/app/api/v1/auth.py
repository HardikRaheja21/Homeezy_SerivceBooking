# backend/app/api/v1/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from app.core.database import get_db
from app.core.config import settings
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, generate_otp, verify_token
from app.core.redis import redis_client
from app.models.user import User, UserRole, AccountStatus
from app.models.customer import CustomerProfile
from app.models.worker import WorkerProfile
from app.services.email_service import EmailService
from datetime import datetime, timezone
import re
import logging

router = APIRouter()
logger = logging.getLogger(__name__)
email_service = EmailService()

class RegisterCustomerRequest(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    password: str
    city: str
    area: str
    pincode: str
    preferred_language: str = "en"
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
    notifications_enabled: bool = True

class RegisterWorkerRequest(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    password: str
    city: str
    area: str
    pincode: str
    service_category: str
    skills: list[str]
    experience_years: int
    government_id_type: str
    government_id_number: str
    working_radius_km: int = 5
    base_charge_per_hour: float
    emergency_available: bool = False
    bank_name: str
    account_number: str
    ifsc_code: str
    emergency_contact_name: str
    emergency_contact_phone: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class OTPVerifyRequest(BaseModel):
    identifier: str  # email or phone
    otp: str
    type: str  # email or phone

class RefreshTokenRequest(BaseModel):
    refresh_token: str

def validate_password(password: str) -> bool:
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False
    return True

def validate_phone(phone: str) -> bool:
    pattern = r"^[+]?[\d\s\-()]+$"
    return bool(re.match(pattern, phone)) and len(re.sub(r"[\s\-()]", "", phone)) >= 10

async def send_otp_email(email: str, otp: str):
    await redis_client.set(f"otp:email:{email}", otp, ex=600)
    if not email_service.send_otp_email(email, otp):
        logger.warning("Failed to send OTP email. email=%s otp=%s", email, otp)

async def send_otp_sms(phone: str, otp: str):
    await redis_client.set(f"otp:phone:{phone}", otp, ex=600)
    try:
        if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN or not settings.TWILIO_PHONE_NUMBER:
            logger.warning("Twilio not configured. phone=%s otp=%s", phone, otp)
            return
        from twilio.rest import Client  # Lazy import — only when Twilio is configured
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=f"Your Homeezy OTP is {otp}. It is valid for 10 minutes.",
            from_=settings.TWILIO_PHONE_NUMBER,
            to=phone,
        )
    except Exception:
        logger.exception("Failed to send OTP SMS. phone=%s", phone)

@router.post("/register/customer")
async def register_customer(
    data: RegisterCustomerRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # Validation
    if not validate_password(data.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be 8+ chars with uppercase, lowercase, number and special char"
        )
    
    if not validate_phone(data.phone):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid phone number"
        )
    
    # Check existing
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    if db.query(User).filter(User.phone == data.phone).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Phone already registered"
        )
    
    # Create user — auto-activate in DEV_MODE, else require OTP verification
    initial_status = AccountStatus.ACTIVE if settings.DEV_MODE else AccountStatus.PENDING
    user = User(
        full_name=data.full_name,
        email=data.email,
        phone=data.phone,
        password_hash=hash_password(data.password),
        role=UserRole.CUSTOMER,
        account_status=initial_status,
        city=data.city,
        area=data.area,
        pincode=data.pincode,
        preferred_language=data.preferred_language
    )
    db.add(user)
    db.flush()
    
    # Create customer profile
    customer_profile = CustomerProfile(
        id=user.id,
        emergency_contact_name=data.emergency_contact_name,
        emergency_contact_phone=data.emergency_contact_phone,
        notifications_enabled=data.notifications_enabled
    )
    db.add(customer_profile)
    db.commit()
    db.refresh(user)
    
    # Skip OTP in DEV_MODE — customers are already active
    if not settings.DEV_MODE:
        email_otp = generate_otp()
        phone_otp = generate_otp()
        background_tasks.add_task(send_otp_email, data.email, email_otp)
        background_tasks.add_task(send_otp_sms, data.phone, phone_otp)
    
    return {
        "message": "Customer registered successfully."
            + (" Account is active (DEV_MODE)." if settings.DEV_MODE
               else " Please verify email and phone."),
        "user_id": user.id,
        "email": user.email,
        "phone": user.phone,
        "dev_mode": settings.DEV_MODE,
    }

@router.post("/register/worker")
async def register_worker(
    data: RegisterWorkerRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # Validation
    if not validate_password(data.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be 8+ chars with uppercase, lowercase, number and special char"
        )
    
    if not validate_phone(data.phone):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid phone number"
        )
    
    if data.experience_years < 0 or data.experience_years > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Experience years must be between 0 and 50"
        )
    
    # Check existing
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    if db.query(User).filter(User.phone == data.phone).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Phone already registered"
        )
    
    # Create user
    user = User(
        full_name=data.full_name,
        email=data.email,
        phone=data.phone,
        password_hash=hash_password(data.password),
        role=UserRole.WORKER,
        account_status=AccountStatus.PENDING,
        city=data.city,
        area=data.area,
        pincode=data.pincode
    )
    db.add(user)
    db.flush()
    
    # Create worker profile
    worker_profile = WorkerProfile(
        id=user.id,
        service_category=data.service_category,
        skills=data.skills,
        experience_years=data.experience_years,
        government_id_type=data.government_id_type,
        government_id_number=data.government_id_number,
        working_radius_km=data.working_radius_km,
        base_charge_per_hour=data.base_charge_per_hour,
        emergency_available=data.emergency_available,
        bank_name=data.bank_name,
        account_number=data.account_number,
        ifsc_code=data.ifsc_code,
        emergency_contact_name=data.emergency_contact_name,
        emergency_contact_phone=data.emergency_contact_phone
    )
    db.add(worker_profile)
    db.commit()
    db.refresh(user)
    
    # Send OTP
    email_otp = generate_otp()
    phone_otp = generate_otp()
    background_tasks.add_task(send_otp_email, data.email, email_otp)
    background_tasks.add_task(send_otp_sms, data.phone, phone_otp)
    
    return {
        "message": "Worker registered successfully. Pending admin approval after verification.",
        "user_id": user.id,
        "email": user.email,
        "phone": user.phone
    }

@router.post("/verify-otp")
async def verify_otp(data: OTPVerifyRequest, db: Session = Depends(get_db)):
    key = f"otp:{data.type}:{data.identifier}"
    attempt_key = f"otp_attempts:{data.type}:{data.identifier}"
    MAX_ATTEMPTS = 5

    stored_otp = await redis_client.get(key)

    if not stored_otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP expired or invalid. Please request a new one."
        )

    # Enforce attempt limit before comparing
    attempts = int(await redis_client.get(attempt_key) or 0)
    if attempts >= MAX_ATTEMPTS:
        await redis_client.delete(key)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed attempts. Please request a new OTP."
        )

    if stored_otp != data.otp:
        new_attempts = attempts + 1
        await redis_client.set(attempt_key, str(new_attempts), ex=600)
        remaining = MAX_ATTEMPTS - new_attempts
        plural = "s" if remaining != 1 else ""
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Incorrect OTP. {remaining} attempt{plural} remaining."
        )

    # OTP is correct — clean up both keys
    await redis_client.delete(key)
    await redis_client.delete(attempt_key)

    # Update user verification
    if data.type == "email":
        user = db.query(User).filter(User.email == data.identifier).first()
        if user:
            user.email_verified = True
    else:
        user = db.query(User).filter(User.phone == data.identifier).first()
        if user:
            user.phone_verified = True

    # Activate account if both verified
    if user and user.email_verified and user.phone_verified:
        if user.role == UserRole.CUSTOMER:
            user.account_status = AccountStatus.ACTIVE
        # Workers stay PENDING until admin approval

    db.commit()

    return {"message": f"{data.type.capitalize()} verified successfully"}

@router.post("/login")
async def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if user.account_status == AccountStatus.BLOCKED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is blocked. Contact support."
        )
    
    if user.account_status == AccountStatus.PENDING:
        if user.role == UserRole.WORKER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account pending admin approval"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Please verify your email and phone"
            )
    
    # Update last login
    user.last_login = datetime.now(timezone.utc)
    db.commit()
    
    # Create tokens
    token_data = {"sub": user.id, "email": user.email, "role": user.role.value}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role.value,
            "profile_photo": user.profile_photo
        }
    }

@router.post("/refresh")
async def refresh_token(data: RefreshTokenRequest, db: Session = Depends(get_db)):
    payload = verify_token(data.refresh_token)
    
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user or user.account_status != AccountStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    token_data = {"sub": user.id, "email": user.email, "role": user.role.value}
    new_access_token = create_access_token(token_data)
    
    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }
