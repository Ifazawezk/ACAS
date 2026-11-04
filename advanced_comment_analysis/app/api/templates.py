from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.template import ResponseTemplate
from app.services.activity_service import record
from app.utils.roles import get_current_user

router = APIRouter(prefix="/admin/templates", tags=["templates"])


class TemplateCreate(BaseModel):
    name: str
    content: str
    description: Optional[str] = None
    category: Optional[str] = None
    is_public: bool = False


class TemplateResponse(BaseModel):
    id: int
    name: str
    content: str
    description: Optional[str] = None
    category: Optional[str] = None
    is_public: Optional[bool] = False
    usage_count: Optional[int] = 0
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True


def find_template(db: Session, template_id: int) -> ResponseTemplate:
    template = db.query(ResponseTemplate).filter(ResponseTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.get("", response_model=List[TemplateResponse])
def list_templates(db: Session = Depends(get_db)):
    """Get all response templates"""
    return db.query(ResponseTemplate).order_by(ResponseTemplate.created_at.desc()).all()


@router.post("", response_model=TemplateResponse)
def create_template(template: TemplateCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Create a new response template"""
    db_template = ResponseTemplate(user_id=user.id, **template.dict())
    db.add(db_template)
    db.flush()
    record(db, user, "create", "template", db_template.id, template.name)
    db.commit()
    db.refresh(db_template)
    return db_template


@router.get("/{template_id}", response_model=TemplateResponse)
def get_template(template_id: int, db: Session = Depends(get_db)):
    """Get a specific template"""
    return find_template(db, template_id)


@router.put("/{template_id}", response_model=TemplateResponse)
def update_template(template_id: int, template: TemplateCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Update a template"""
    db_template = find_template(db, template_id)
    for field, value in template.dict().items():
        setattr(db_template, field, value)
    record(db, user, "update", "template", template_id, template.name)
    db.commit()
    db.refresh(db_template)
    return db_template


@router.delete("/{template_id}")
def delete_template(template_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Delete a template"""
    db_template = find_template(db, template_id)
    record(db, user, "delete", "template", template_id, db_template.name)
    db.delete(db_template)
    db.commit()
    return {"message": "Template deleted"}


@router.post("/{template_id}/use", response_model=TemplateResponse)
def use_template(template_id: int, db: Session = Depends(get_db)):
    """Increment usage count for a template"""
    db_template = find_template(db, template_id)
    db_template.usage_count = (db_template.usage_count or 0) + 1
    db.commit()
    db.refresh(db_template)
    return db_template
