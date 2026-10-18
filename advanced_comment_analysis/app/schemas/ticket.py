from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class TicketStatus(str, Enum):
    open = "open"
    in_progress = "in_progress"
    closed = "closed"


class TicketCreate(BaseModel):
    comment_id: int
    title: str
    description: Optional[str]
    priority: str
    assigned_to: Optional[int]


class TicketRead(BaseModel):
    id: int
    comment_id: int
    title: str
    description: Optional[str]
    status: TicketStatus
    priority: str
    assigned_to: Optional[int]
    created_at: Optional[datetime]
    closed_at: Optional[datetime]

    class Config:
        orm_mode = True
