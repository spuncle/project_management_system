from flask_login import current_user
from .models import ActivityLog
from . import db

def log_activity(action, details=""):
    """
    Helper function to create and save an activity log.
    """
    if current_user.is_authenticated:
        log = ActivityLog(
            user_id=current_user.id,
            action=action,
            details=details
        )
        db.session.add(log)
        db.session.commit()
