from .models import ActivityLog
import json


#Create an activity log entry
"""
    Args:
        user: User performing the action
        activity_type: Type of activity (from ActivityLog.ActivityType)
        object_type: The model or object being acted upon
"""
def log_activity(user, activity_type, object_type, details=None):

    try:
        if details and not isinstance(details, dict):
            try:
                details = json.loads(details)
            except (TypeError, json.JSONDecodeError):
                details = {"data": str(details)}

        ActivityLog.objects.create(
            user=user,
            activity_type=activity_type,
            object_type=object_type,
        )
    except Exception as e:
        print(f"Error logging activity: {str(e)}")