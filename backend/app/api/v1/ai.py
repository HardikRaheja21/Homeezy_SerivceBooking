from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import require_role
from app.models.user import User, UserRole
from app.core.redis import redis_client
from app.core.rate_limiter import RateLimiter

# New AI Architecture
from app.ai.schemas import ChatRequest
from app.ai.services.chat import AIChatService

# Keep old orchestrator imports temporarily until fully refactored, but move them to new location if possible.
from app.agents.orchestrator import AgentOrchestrator
from app.agents.provider_recommendation_agent import ProviderMatchingAgent

router = APIRouter()
orchestrator = AgentOrchestrator()
matching_agent = ProviderMatchingAgent()

@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest, 
    http_request: Request,
    current_user: User = Depends(require_role([UserRole.CUSTOMER, UserRole.WORKER, UserRole.ADMIN]))
):
    """
    Stream AI responses using Server-Sent Events (SSE).
    Protected by AI-specific rate limiter.
    """
    limiter = RateLimiter(redis_client)
    identifier = str(current_user.id) if current_user else http_request.client.host
    
    is_allowed = await limiter.check_ai_rate_limit(identifier, is_authenticated=bool(current_user))
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="AI usage limit exceeded. Please try again later."
        )

    chat_service = AIChatService()
    
    async def event_generator():
        tokens = 0
        async for chunk in chat_service.stream_chat(request.message, request.history):
            tokens += 1
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"
        
        # Roughly track token usage (1 token ~= 4 chars typically, but here we count chunks)
        await limiter.track_ai_tokens(identifier, estimated_tokens=tokens * 2)
        
    return StreamingResponse(event_generator(), media_type="text/event-stream")

class ProviderRecommendationRequest(BaseModel):
    service_category: str
    customer_lat: float
    customer_lng: float
    max_candidates: int = Field(default=20, ge=1, le=100)

@router.post("/recommend-provider")
async def recommend_provider(
    data: ProviderRecommendationRequest,
    db: Session = Depends(get_db),
):
    items = matching_agent.recommend(
        db=db,
        service_category=data.service_category,
        customer_lat=data.customer_lat,
        customer_lng=data.customer_lng,
        max_candidates=data.max_candidates,
    )
    return {"items": items, "count": len(items)}

class AIRecommendationRequest(BaseModel):
    service_category: str
    service_description: str = ""
    skills_required: list[str] = []
    estimated_duration_hours: float = Field(default=2.0, gt=0)
    demand_index: float = Field(default=1.0, ge=0.5, le=2.0)

@router.post("/recommend")
async def recommend_providers(
    data: AIRecommendationRequest,
    db: Session = Depends(get_db),
):
    recommendation = orchestrator.recommend(db=db, payload=data.model_dump())
    return recommendation

@router.get("/admin-insights")
async def get_admin_ai_insights(
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db),
):
    _ = current_user
    return orchestrator.admin_insights(db)

