from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.database.session import Base


class SenticMapping(Base):
    __tablename__ = 'sentic_mappings'

    id = Column(Integer, primary_key=True, index=True)
    emotion = Column(String(200), nullable=False)
    priority = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
