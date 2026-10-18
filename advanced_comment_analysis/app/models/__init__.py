# models package
# Import all models to ensure SQLAlchemy creates all tables
from app.models.user import User, Base
from app.models.comment import Comment
from app.models.ticket import Ticket
from app.models.routing_rule import RoutingRule
from app.models.sentic_mapping import SenticMapping
from app.models.setting import Setting
from app.models.api_config import APIConfig
from app.models.activity_log import ActivityLog, Favorite
from app.models.template import ResponseTemplate

__all__ = [
    'Base',
    'User',
    'Comment',
    'Ticket',
    'RoutingRule',
    'SenticMapping',
    'Setting',
    'APIConfig',
    'ActivityLog',
    'Favorite',
    'ResponseTemplate'
]
