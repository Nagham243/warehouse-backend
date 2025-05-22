# urls.py
from django.urls import path
from . import views
from accounts import auth_views

urlpatterns = [
    # Authentication endpoints
    path('api/auth-status/', views.check_auth_status, name='auth_status'),
    path('api/csrf-token/', views.csrf_token, name='csrf_token'),
    path('api/login/', auth_views.login_view, name='api_login'),
    path('api/logout/', auth_views.logout_view, name='api_logout'),

    # Your existing URLs...
]