"""
API Configuration model for storing third-party API keys and credentials
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import json

Base = declarative_base()


class APIConfig(Base):
    __tablename__ = "api_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)  # e.g., "openai", "huggingface"
    provider = Column(String(100), nullable=False)  # e.g., "OpenAI", "HuggingFace"
    api_key = Column(Text, nullable=False)  # Encrypted in production
    api_url = Column(String(500), nullable=True)  # Optional custom endpoint
    model_name = Column(String(200), nullable=True)  # e.g., "gpt-4o" for OpenAI
    config_json = Column(Text, nullable=True)  # Additional config as JSON
    is_active = Column(Boolean, default=True)
    is_configured = Column(Boolean, default=True)
    last_tested = Column(DateTime, nullable=True)
    test_status = Column(String(20), default="unknown")  # unknown, success, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self, include_key=False):
        """Convert to dictionary, optionally hiding API key"""
        return {
            "id": self.id,
            "name": self.name,
            "provider": self.provider,
            "api_key": self.api_key if include_key else "***" * 5,  # Mask key by default
            "api_url": self.api_url,
            "model_name": self.model_name,
            "is_active": self.is_active,
            "is_configured": self.is_configured,
            "last_tested": self.last_tested.isoformat() if self.last_tested else None,
            "test_status": self.test_status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
