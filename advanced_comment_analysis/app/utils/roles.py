from fastapi import Depends, HTTPException, status
from app.api.auth import get_current_user
from app.models.user import UserRole


def require_role(role: UserRole):
    def _require(user = Depends(get_current_user)):
        if user.role != role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient privileges")
        return user
    return _require
