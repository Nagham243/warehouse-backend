# middleware.py
from django.http import JsonResponse
from rest_framework import status
from django.utils.deprecation import MiddlewareMixin

class AuthenticationMiddleware(MiddlewareMixin):
    """
    Middleware to provide better feedback for authentication failures
    """
    def process_response(self, request, response):
        # Check if the response is a 403 Forbidden
        if response.status_code == 403 and hasattr(request, 'user') and not request.user.is_authenticated:
            # Override with a more descriptive JSON response
            return JsonResponse({
                'error': 'Authentication required',
                'message': 'Your session has expired or you are not logged in.',
                'code': 'auth_required'
            }, status=status.HTTP_403_FORBIDDEN)
        return response