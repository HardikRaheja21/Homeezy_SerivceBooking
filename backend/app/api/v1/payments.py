from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.config import settings
from app.models.user import User
from app.models.booking import Booking, BookingStatus, PaymentStatus
from app.models.payment import Payment, PaymentMethod
from app.models.worker import WorkerProfile
from app.services.payment_service import PaymentService

router = APIRouter()
payment_service = PaymentService()


class InitiatePaymentRequest(BaseModel):
    booking_id: str
    payment_method: PaymentMethod


class VerifyPaymentRequest(BaseModel):
    booking_id: str
    gateway_order_id: str
    gateway_transaction_id: str
    signature: str


@router.post("/initiate")
async def initiate_payment(
    data: InitiatePaymentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    booking = db.query(Booking).filter(Booking.id == data.booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if booking.status != BookingStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Can only pay for completed bookings")
    if booking.payment_status == PaymentStatus.PAID:
        raise HTTPException(status_code=400, detail="Already paid")

    final_price = booking.final_price or booking.estimated_price
    commission_payload = payment_service.calculate_platform_commission(final_price)
    booking.platform_commission = commission_payload["commission"]
    booking.worker_payout = commission_payload["worker_payout"]

    payment = Payment(
        booking_id=booking.id,
        amount=final_price,
        payment_method=data.payment_method,
        status="pending",
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    gateway_order_id = f"test_order_{payment.id}"
    gateway_response = {"mode": "simulated"}
    if payment_service.razorpay_client and data.payment_method != PaymentMethod.CASH:
        order = payment_service.create_razorpay_order(amount=final_price, receipt=payment.id)
        gateway_order_id = order["id"]
        gateway_response = order

    payment.gateway_order_id = gateway_order_id
    payment.gateway_response = gateway_response
    db.commit()

    return {
        "payment_id": payment.id,
        "gateway_order_id": gateway_order_id,
        "amount": final_price,
        "currency": "INR",
        "razorpay_key_id": settings.RAZORPAY_KEY_ID,
    }


@router.post("/verify")
async def verify_payment(
    data: VerifyPaymentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    booking = db.query(Booking).filter(Booking.id == data.booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    payment = db.query(Payment).filter(Payment.booking_id == booking.id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    if payment.gateway_order_id != data.gateway_order_id:
        raise HTTPException(status_code=400, detail="Order ID mismatch")

    verified = False
    if payment_service.razorpay_client:
        verified = payment_service.verify_razorpay_signature(
            order_id=data.gateway_order_id,
            payment_id=data.gateway_transaction_id,
            signature=data.signature,
        )
    else:
        verified = data.signature == "test_signature"

    if not verified:
        raise HTTPException(status_code=400, detail="Invalid payment signature")

    payment.gateway_transaction_id = data.gateway_transaction_id
    payment.status = "success"
    payment.completed_at = datetime.now(timezone.utc)
    booking.payment_status = PaymentStatus.PAID

    if booking.worker_id:
        worker_profile = db.query(WorkerProfile).filter(WorkerProfile.id == booking.worker_id).first()
        if worker_profile:
            worker_profile.total_earnings += booking.worker_payout or 0.0
            worker_profile.total_jobs_completed += 1

    db.commit()
    return {"message": "Payment verified successfully", "status": "success", "amount": payment.amount}


@router.post("/refund/{booking_id}")
async def request_refund(
    booking_id: str,
    reason: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if booking.status != BookingStatus.CANCELLED:
        raise HTTPException(status_code=400, detail="Can only refund cancelled bookings")

    payment = db.query(Payment).filter(Payment.booking_id == booking.id).first()
    if not payment or payment.status != "success":
        raise HTTPException(status_code=400, detail="No successful payment found")

    refund_amount = round(payment.amount * 0.8, 2)
    if payment_service.razorpay_client and payment.gateway_transaction_id:
        payment_service.create_razorpay_refund(payment.gateway_transaction_id, refund_amount)

    payment.refund_amount = refund_amount
    payment.refund_reason = reason
    payment.refunded_at = datetime.now(timezone.utc)
    payment.status = "refunded"
    booking.payment_status = PaymentStatus.REFUNDED
    db.commit()

    return {"message": "Refund processed successfully", "refund_amount": refund_amount}


from fastapi import Request
import hmac as hmac_lib
import hashlib

@router.post("/webhook")
async def razorpay_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Handles Razorpay webhook events securely via atomic HMAC-SHA256 verification.
    Fails closed: if the secret is not configured, all webhooks are rejected.
    """
    # Fail closed: reject if secret is not configured
    if not settings.RAZORPAY_KEY_SECRET:
        raise HTTPException(status_code=503, detail="Payment webhook not configured")

    body = await request.body()
    signature = request.headers.get("x-razorpay-signature", "")

    if not signature:
        raise HTTPException(status_code=400, detail="Missing webhook signature")

    # Atomic HMAC-SHA256 verification — no early-exit before compare_digest
    try:
        expected_signature = hmac_lib.new(
            settings.RAZORPAY_KEY_SECRET.encode("utf-8"),
            msg=body,
            digestmod=hashlib.sha256,
        ).hexdigest()
    except Exception:
        raise HTTPException(status_code=400, detail="Signature computation failed")

    if not hmac_lib.compare_digest(expected_signature, signature):
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    # Parse and handle verified event
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event = payload.get("event", "")

    if event == "payment.captured":
        payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
        gateway_payment_id = payment_entity.get("id")
        gateway_order_id = payment_entity.get("order_id")

        if gateway_order_id:
            payment = db.query(Payment).filter(
                Payment.gateway_order_id == gateway_order_id
            ).first()
            if payment and payment.status != "success":
                from app.models.booking import PaymentStatus
                payment.status = "success"
                payment.gateway_transaction_id = gateway_payment_id
                booking = db.query(Booking).filter(Booking.id == payment.booking_id).first()
                if booking:
                    booking.payment_status = PaymentStatus.PAID
                db.commit()

    return {"status": "ok"}

