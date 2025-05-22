from django.utils.deprecation import MiddlewareMixin
from .utils import log_activity
from django.urls import resolve

class ActivityLogMiddleware(MiddlewareMixin):
    """Middleware to log user activities based on specific API endpoints"""

    def __init__(self, get_response):
        self.get_response = get_response
        self.tracked_urls = {
            # Format: 'url_name': {'activity_type': 'type', 'object_type': 'type'}
            'user-list': {'activity_type': 'view', 'object_type': 'User'},
            'user-detail': {'activity_type': 'view', 'object_type': 'User'},
            'user-create': {'activity_type': 'create', 'object_type': 'User'},
            'user-update': {'activity_type': 'update', 'object_type': 'User'},
            'user-delete': {'activity_type': 'delete', 'object_type': 'User'},
            'user-suspend': {'activity_type': 'suspend', 'object_type': 'User'},
            'user-activate': {'activity_type': 'activate', 'object_type': 'User'},
        }

    def process_view(self, request, view_func, view_args, view_kwargs):
        """Process view is called just before Django calls the view"""
        if not request.user.is_authenticated:
            return None

        url_name = resolve(request.path_info).url_name

        if url_name in self.tracked_urls:
            config = self.tracked_urls[url_name]

            log_activity(
                user=request.user,
                activity_type=config['activity_type'],
                object_type=config['object_type'],
            )

        return None
