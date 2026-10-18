from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, JSON, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.database.session import Base


class PriorityLevel(str, enum.Enum):
    Low = "Low"
    Medium = "Medium"
    High = "High"
    Critical = "Critical"


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String(255), nullable=True)
    source = Column(String(100), nullable=True)
    content = Column(Text, nullable=False)
    raw_metadata = Column(JSON, nullable=True)

    emotion = Column(String(100), nullable=True)
    intent = Column(String(255), nullable=True)
    priority = Column(Enum(PriorityLevel), default=PriorityLevel.Low, nullable=False)
    needs_ticket = Column(Boolean, default=False, nullable=False)
    suggested_response = Column(Text, nullable=True)
    confidence = Column(Float, default=0.0, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    analyzed_at = Column(DateTime(timezone=True), nullable=True)

    ticket = relationship("Ticket", back_populates="comment", uselist=False)
