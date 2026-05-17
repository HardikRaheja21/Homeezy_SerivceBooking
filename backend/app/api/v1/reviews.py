from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.review import Review
from app.models.booking import Booking, BookingStatus
from app.services.ai_service import AIService

router = APIRouter()
ai_service = AIService()

class CreateReviewRequest(BaseModel):
    booking_id: str
    rating: int  # 1-5
    review_text: str

@router.post("/create")
async def create_review(
    data: CreateReviewRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Validate rating
    if not 1 <= data.rating <= 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rating must be between 1 and 5"
        )
    
    # Get booking
    booking = db.query(Booking).filter(Booking.id == data.booking_id).first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if booking.status != BookingStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail="Can only review completed bookings"
        )
    
    # Check if user is part of the booking
    if booking.customer_id != current_user.id and booking.worker_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Check if review already exists
    existing = db.query(Review).filter(
        Review.booking_id == data.booking_id,
        Review.reviewer_id == current_user.id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Review already submitted")
    
    # Determine who is being reviewed
    reviewed_user_id = booking.worker_id if current_user.id == booking.customer_id else booking.customer_id
    
    # AI Sentiment Analysis
    sentiment = await ai_service.analyze_review_sentiment(data.review_text)
    
    # Create review
    review = Review(
        booking_id=data.booking_id,
        reviewer_id=current_user.id,
        reviewed_user_id=reviewed_user_id,
        rating=data.rating,
        review_text=data.review_text,
        sentiment_score=sentiment["sentiment_score"],
        sentiment_label=sentiment["sentiment_label"],
        key_phrases=sentiment["key_phrases"]
    )
    
    db.add(review)
    db.commit()
    
    # Update worker's average rating if worker was reviewed
    if current_user.id == booking.customer_id:
        from app.models.worker import WorkerProfile
        worker_profile = db.query(WorkerProfile).filter(
            WorkerProfile.id == booking.worker_id
        ).first()
        
        if worker_profile:
            # Recalculate average rating
            all_reviews = db.query(Review).filter(
                Review.reviewed_user_id == booking.worker_id
            ).all()
            
            if all_reviews:
                avg_rating = sum(r.rating for r in all_reviews) / len(all_reviews)
                worker_profile.average_rating = avg_rating
                worker_profile.total_reviews = len(all_reviews)
                db.commit()
    
    return {
        "message": "Review submitted successfully",
        "review_id": review.id,
        "sentiment": sentiment["sentiment_label"]
    }

@router.get("/user/{user_id}")
async def get_user_reviews(
    user_id: str,
    db: Session = Depends(get_db)
):
    reviews = db.query(Review).filter(
        Review.reviewed_user_id == user_id
    ).order_by(Review.created_at.desc()).all()
    
    return [
        {
            "id": r.id,
            "rating": r.rating,
            "review_text": r.review_text,
            "reviewer_name": r.reviewer.full_name,
            "sentiment_label": r.sentiment_label,
            "key_phrases": r.key_phrases,
            "created_at": r.created_at,
            "helpful_count": r.helpful_count
        }
        for r in reviews
    ]