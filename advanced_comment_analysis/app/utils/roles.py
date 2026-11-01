"""Who may call what. enforce_access runs on every route, so these rules live in one place."""
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User, UserRole
from app.utils import security

PUBLIC = "public"
AUTHENTICATED = "authenticated"
ADMIN = "admin"

# The only routes that answer without a token. A route is closed unless it is listed here.
PUBLIC_ROUTES = {
    ("POST", "/auth/register"),
    ("POST", "/auth/token"),
    ("GET", "/health"),
}

# Admin routes outside the /admin paths. Everything under /admin is admin-only already.
ADMIN_ROUTES = {
    ("POST", "/comments/bulk-action"),
    ("GET", "/comments/export/download"),
    ("GET", "/comments/activity/log"),
}

bearer_scheme = HTTPBearer(auto_error=False)


def access_rule(method: str, path: str) -> str:
    """Return the rule for a route, where path is its template, such as /comments/{comment_id}."""
    if (method, path) in PUBLIC_ROUTES:
        return PUBLIC
    if path.startswith("/admin") or (method, path) in ADMIN_ROUTES:
        return ADMIN
    return AUTHENTICATED


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """The logged-in user. Answers 401 unless the token is valid and the account is active."""
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized
    try:
        payload = security.decode_access_token(credentials.credentials)
        user_id = int(payload.get("sub"))
    except Exception:
        raise unauthorized
    # The role and the active flag come from the database, never from the token.
    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        raise unauthorized
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    """The logged-in user, who must be an admin. Answers 403 for anyone else."""
    if user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient privileges")
    return user


def enforce_access(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> None:
    """Set on the whole app in main.py, so a new route is closed without any extra code."""
    rule = access_rule(request.method, request.scope["route"].path)
    if rule == PUBLIC:
        return
    user = get_current_user(credentials, db)
    if rule == ADMIN:
        require_admin(user)
