from pydantic import BaseModel, EmailStr
from typing import Optional


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str
    role: str


class TokenData(BaseModel):
    user_id: Optional[int] = None


class UserRegister(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    password: str
    role: str = "user"  # default to user, can be: user, manager, admin


class UserLogin(BaseModel):
    username: str
    password: str


class UserRead(BaseModel):
    id: int
    username: str
    email: Optional[str]
    role: str
    is_active: bool
    
    class Config:
        orm_mode = True
