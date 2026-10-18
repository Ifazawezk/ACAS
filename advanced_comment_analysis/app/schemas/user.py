from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    admin = "admin"
    support = "support"


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: UserRole = UserRole.support


class UserRead(BaseModel):
    id: int
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: Optional[datetime]

    class Config:
        orm_mode = True
