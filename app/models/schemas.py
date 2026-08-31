from typing import Literal, Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str = Field(..., description="Client-generated conversation id")
    message: str = Field(..., min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    escalated: bool = False
    escalation_reason: Optional[str] = None
    used_recommendation_engine: bool = False


class Recommendation(BaseModel):
    exercise: str
    rationale: str
    confidence: float
    source: Literal["mock_recommendation_engine"] = "mock_recommendation_engine"
