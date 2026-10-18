from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.user import Base

class ResponseTemplate(Base):
    """Response templates for quick replies to common comment types"""
    __tablename__ = "response_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    content = Column(Text, nullable=False)
    category = Column(String(100))  # e.g., "angry_customer", "feature_request", "bug"
    is_public = Column(Boolean, default=False)
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.utcnow(), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())
    
    # Relationships
    user = relationship("User", back_populates="templates")
