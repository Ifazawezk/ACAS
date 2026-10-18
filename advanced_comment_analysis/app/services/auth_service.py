from sqlalchemy.orm import Session
from app.models.user import User, UserRole
from app.schemas.auth import UserRegister
from app.utils.security import hash_password, verify_password, create_access_token
from app.utils.security import decode_access_token
from app.models.user import User


def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, user_in: UserRegister):
    hashed = hash_password(user_in.password)
    role = UserRole(user_in.role) if user_in.role in [r.value for r in UserRole] else UserRole.user
    user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hashed,
        role=role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        return None
    # create JWT
    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return token, user


def get_user_from_token(db: Session, token: str):
    """Decode JWT token and return User or None"""
    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("sub"))
    except Exception:
        return None
    return db.query(User).filter(User.id == user_id).first()
