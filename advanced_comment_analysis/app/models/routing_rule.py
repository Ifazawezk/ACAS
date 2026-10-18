from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.database.session import Base


class RoutingRule(Base):
    __tablename__ = 'routing_rules'

    id = Column(Integer, primary_key=True, index=True)
    pattern = Column(String(1000), nullable=False)
    priority = Column(String(50), nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
