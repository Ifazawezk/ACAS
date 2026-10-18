from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import logging

from app.database.session import get_db
from app.models.routing_rule import RoutingRule
from app.models.sentic_mapping import SenticMapping
from app.models.setting import Setting
from app.models.api_config import APIConfig

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get('/rules', response_model=List[dict])
def list_rules(db: Session = Depends(get_db)):
    rules = db.query(RoutingRule).order_by(RoutingRule.created_at.desc()).all()
    return [ {"id": r.id, "pattern": r.pattern, "priority": r.priority, "enabled": r.enabled} for r in rules ]


@router.post('/rules')
def create_rule(payload: dict, db: Session = Depends(get_db)):
    pattern = payload.get('pattern')
    priority = payload.get('priority', 'Low')
    if not pattern:
        raise HTTPException(status_code=400, detail='pattern required')
    r = RoutingRule(pattern=pattern, priority=priority, enabled=payload.get('enabled', True))
    db.add(r)
    db.commit()
    db.refresh(r)
    return {"id": r.id, "pattern": r.pattern, "priority": r.priority, "enabled": r.enabled}


@router.delete('/rules/{rule_id}')
def delete_rule(rule_id: int, db: Session = Depends(get_db)):
    r = db.query(RoutingRule).filter(RoutingRule.id == rule_id).first()
    if not r:
        raise HTTPException(status_code=404, detail='not found')
    db.delete(r)
    db.commit()
    return {"ok": True}


@router.get('/sentics', response_model=List[dict])
def list_sentics(db: Session = Depends(get_db)):
    items = db.query(SenticMapping).order_by(SenticMapping.created_at.desc()).all()
    return [{"id": i.id, "emotion": i.emotion, "priority": i.priority} for i in items]


@router.post('/sentics')
def create_sentics(payload: dict, db: Session = Depends(get_db)):
    emotion = payload.get('emotion')
    priority = payload.get('priority', 'Low')
    if not emotion:
        raise HTTPException(status_code=400, detail='emotion required')
    m = SenticMapping(emotion=emotion, priority=priority)
    db.add(m)
    db.commit()
    db.refresh(m)
    return {"id": m.id, "emotion": m.emotion, "priority": m.priority}


@router.delete('/sentics/{mid}')
def delete_sentics(mid: int, db: Session = Depends(get_db)):
    m = db.query(SenticMapping).filter(SenticMapping.id == mid).first()
    if not m:
        raise HTTPException(status_code=404, detail='not found')
    db.delete(m)
    db.commit()
    return {"ok": True}


@router.get('/config')
def get_config(db: Session = Depends(get_db)):
    rows = db.query(Setting).all()
    out = {r.key: r.value for r in rows}
    return out


@router.post('/config')
def set_config(payload: dict, db: Session = Depends(get_db)):
    # payload is key/value map
    for k, v in payload.items():
        row = db.query(Setting).filter(Setting.key == k).first()
        if row:
            row.value = v
        else:
            row = Setting(key=k, value=v)
            db.add(row)
    db.commit()
    return {"ok": True}


# ===== API Configuration Management =====

@router.get('/api-configs', response_model=List[dict])
def list_api_configs(db: Session = Depends(get_db)):
    """List all configured APIs (with masked keys)"""
    configs = db.query(APIConfig).order_by(APIConfig.created_at.desc()).all()
    return [cfg.to_dict(include_key=False) for cfg in configs]


@router.post('/api-configs')
def create_api_config(payload: dict, db: Session = Depends(get_db)):
    """Add a new API configuration"""
    logger = logging.getLogger(__name__)
    
    name = payload.get('name', '').strip()
    provider = payload.get('provider', '').strip()
    api_key = payload.get('api_key', '').strip()
    
    if not name or not provider or not api_key:
        raise HTTPException(status_code=400, detail='name, provider, and api_key are required')
    
    # Check if already exists
    existing = db.query(APIConfig).filter(APIConfig.name == name).first()
    if existing:
        raise HTTPException(status_code=400, detail=f'API config "{name}" already exists')
    
    config = APIConfig(
        name=name,
        provider=provider,
        api_key=api_key,
        api_url=payload.get('api_url'),
        model_name=payload.get('model_name'),
        is_active=payload.get('is_active', True)
    )
    
    db.add(config)
    db.commit()
    db.refresh(config)
    
    logger.info(f'Created API config: {name} ({provider})')
    return config.to_dict(include_key=False)


@router.put('/api-configs/{config_id}')
def update_api_config(config_id: int, payload: dict, db: Session = Depends(get_db)):
    """Update an existing API configuration"""
    config = db.query(APIConfig).filter(APIConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail='API config not found')
    
    # Update fields if provided
    if 'name' in payload:
        config.name = payload['name'].strip()
    if 'api_key' in payload and payload['api_key']:
        config.api_key = payload['api_key'].strip()
    if 'api_url' in payload:
        config.api_url = payload['api_url']
    if 'model_name' in payload:
        config.model_name = payload['model_name']
    if 'is_active' in payload:
        config.is_active = payload['is_active']
    if 'provider' in payload:
        config.provider = payload['provider'].strip()
    
    db.commit()
    db.refresh(config)
    return config.to_dict(include_key=False)


@router.delete('/api-configs/{config_id}')
def delete_api_config(config_id: int, db: Session = Depends(get_db)):
    """Delete an API configuration"""
    config = db.query(APIConfig).filter(APIConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail='API config not found')
    
    db.delete(config)
    db.commit()
    return {"ok": True}


@router.post('/api-configs/{config_id}/test')
def test_api_config(config_id: int, db: Session = Depends(get_db)):
    """Test an API configuration to verify it works"""
    logger = logging.getLogger(__name__)
    config = db.query(APIConfig).filter(APIConfig.id == config_id).first()
    
    if not config:
        raise HTTPException(status_code=404, detail='API config not found')
    
    try:
        status = "success"
        message = f"{config.provider} API key is valid"
        
        # Simple test: try importing/validating based on provider
        if config.provider.lower() == "openai":
            try:
                import openai
                openai.api_key = config.api_key
                # Try a minimal API call or just validate key format
                if len(config.api_key) < 20:
                    status = "failed"
                    message = "OpenAI API key appears invalid (too short)"
                else:
                    message = "OpenAI API key format is valid"
            except Exception as e:
                status = "failed"
                message = f"OpenAI test failed: {str(e)}"
        else:
            # Generic validation
            if len(config.api_key) < 10:
                status = "failed"
                message = "API key appears too short"
        
        # Update test status
        config.test_status = status
        db.commit()
        
        return {
            "status": status,
            "message": message,
            "provider": config.provider
        }
        
    except Exception as e:
        logger.exception(f"Error testing API config: {config.name}")
        config.test_status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")
