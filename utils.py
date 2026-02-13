"""
Utility functions for Task Planner
"""
import json
from typing import Any, Optional
from models import db, Activity


def log_activity(user_id: int, action: str, entity_type: str, entity_id: int, details: Optional[dict] = None) -> None:
    """Log user activity"""
    details_json = json.dumps(details) if details else None
    activity = Activity(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details_json
    )
    db.session.add(activity)
    db.session.commit()


def notify_mentions(task_id: int, mentions: list, author_id: int, content: str) -> None:
    """Process mentions in comments"""
    from models import User
    if mentions:
        for mention in mentions:
            mention_user = User.query.get(mention)
            if mention_user and mention_user.id != author_id:
                # In production, send notification email/push
                pass
