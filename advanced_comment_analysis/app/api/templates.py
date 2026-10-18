from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.template import ResponseTemplate
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/admin/templates", tags=["templates"])

class TemplateCreate(BaseModel):
    name: str
    content: str
    description: str = None
    category: str = None
    is_public: bool = False

class TemplateResponse(BaseModel):
    id: int
    name: str
    content: str
    category: str = None
    usage_count: int = 0
    created_at: str = None

@router.get("", response_model=List[TemplateResponse])
async def list_templates(db: Session = Depends(get_db)):
    """Get all response templates"""
    templates = db.query(ResponseTemplate).all()
    return templates

@router.post("", response_model=TemplateResponse)
async def create_template(template: TemplateCreate, db: Session = Depends(get_db)):
    """Create a new response template"""
    db_template = ResponseTemplate(
        user_id=1,  # TODO: Get from auth context
        name=template.name,
        content=template.content,
        description=template.description,
        category=template.category,
        is_public=template.is_public
    )
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template

@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(template_id: int, db: Session = Depends(get_db)):
    """Get a specific template"""
    template = db.query(ResponseTemplate).filter(ResponseTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template

@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(template_id: int, template: TemplateCreate, db: Session = Depends(get_db)):
    """Update a template"""
    db_template = db.query(ResponseTemplate).filter(ResponseTemplate.id == template_id).first()
    if not db_template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    db_template.name = template.name
    db_template.content = template.content
    db_template.description = template.description
    db_template.category = template.category
    
    db.commit()
    db.refresh(db_template)
    return db_template

@router.delete("/{template_id}")
async def delete_template(template_id: int, db: Session = Depends(get_db)):
    """Delete a template"""
    db_template = db.query(ResponseTemplate).filter(ResponseTemplate.id == template_id).first()
    if not db_template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    db.delete(db_template)
    db.commit()
    return {"message": "Template deleted"}

@router.post("/{template_id}/use")
async def use_template(template_id: int, db: Session = Depends(get_db)):
    """Increment usage count for a template"""
    db_template = db.query(ResponseTemplate).filter(ResponseTemplate.id == template_id).first()
    if not db_template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    db_template.usage_count += 1
    db.commit()
    db.refresh(db_template)
    return db_template
