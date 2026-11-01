from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.auth import UserRegister, UserLogin, Token, UserRead
from app.services import auth_service
from app.database.session import get_db
from app.utils import security
from app.utils.roles import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token)
def register(user_in: UserRegister, db: Session = Depends(get_db)):
    """Register a new user account"""
    # Validate username length
    if len(user_in.username) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username must be at least 3 characters long"
        )
    
    # Check username availability
    existing = auth_service.get_user_by_username(db, user_in.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken. Please choose a different username."
        )
    
    # Check email if provided
    if user_in.email:
        if "@" not in user_in.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format"
            )
        email_exists = auth_service.get_user_by_email(db, user_in.email)
        if email_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered with another account"
            )
    
    # Validate password strength
    if len(user_in.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long"
        )
    if len(user_in.password.encode('utf-8')) > security.MAX_PASSWORD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password must be at most {security.MAX_PASSWORD_BYTES} bytes long"
        )
    
    user = auth_service.create_user(db, user_in)
    token = security.create_access_token({"sub": str(user.id), "role": user.role.value})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username,
        "role": user.role.value
    }


@router.post("/token", response_model=Token)
def login(form_data: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and return access token"""
    if not form_data.username or not form_data.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username and password are required"
        )
    
    result = auth_service.authenticate_user(db, form_data.username, form_data.password)
    if not result:
        # Don't reveal which field is wrong for security
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials. Please check your username and password."
        )
    
    token, user = result
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username,
        "role": user.role.value
    }


@router.get("/me", response_model=UserRead)
def get_me(user: User = Depends(get_current_user)):
    return user
