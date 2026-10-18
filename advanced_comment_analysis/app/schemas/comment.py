from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime
from enum import Enum


class PriorityLevel(str, Enum):
    Low = "Low"
    Medium = "Medium"
    High = "High"
    Critical = "Critical"


class CommentCreate(BaseModel):
    customer_name: Optional[str]
    source: Optional[str]
    content: str
    raw_metadata: Optional[Any]


class CommentAnalysis(BaseModel):
    emotion: Optional[str]
    intent: Optional[str]
    priority: Optional[PriorityLevel]
    needs_ticket: Optional[bool]
    suggested_response: Optional[str]
    confidence: Optional[float]


class CommentRead(BaseModel):
    id: int
    customer_name: Optional[str]
    source: Optional[str]
    content: str
    raw_metadata: Optional[Any]
    emotion: Optional[str]
    intent: Optional[str]
    priority: Optional[PriorityLevel]
    needs_ticket: Optional[bool]
    suggested_response: Optional[str]
    confidence: Optional[float]
    created_at: Optional[datetime]
    analyzed_at: Optional[datetime]

    class Config:
        orm_mode = True
