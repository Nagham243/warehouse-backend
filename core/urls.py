"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import routers
from accounts.auth_views import (
    CSRFTokenView, LoginView, LogoutView,
    PasswordChangeView, UserProfileView,RegistrationView
)
from superadmin.views import UserManagementViewSet,CategoryManagementViewSet, SubCategoryManagementViewSet,VendorManagementViewSet,DealManagementViewSet, OfferManagementViewSet,CommissionManagementViewSet
from activity_logs.views import ActivityLogViewSet
from accounts.views import SuperAdminProfileView

router = routers.DefaultRouter()
router.register(r'users', UserManagementViewSet, basename='user')
router.register(r'activities', ActivityLogViewSet, basename='activity')
router.register(r'categories', CategoryManagementViewSet, basename='category')
router.register(r'subcategories', SubCategoryManagementViewSet, basename='subcategory')
router.register(r'vendors', VendorManagementViewSet, basename='vendor')
router.register(r'deals', DealManagementViewSet, basename='deal')
router.register(r'offers', OfferManagementViewSet, basename='offer')
router.register(r'commissions', CommissionManagementViewSet, basename='commission')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/csrf-token/', CSRFTokenView.as_view(), name='csrf-token'),
    path('api/login/', LoginView.as_view(), name='login'),
    path('api/logout/', LogoutView.as_view(), name='logout'),
    path('api/password-change/', PasswordChangeView.as_view(), name='password-change'),
    path('api/me/', UserProfileView.as_view(), name='me'),
    path('api/', include(router.urls)),
    path('vendor/register/', RegistrationView.as_view(), name='vendor-registration'),
    path('api/profile/', SuperAdminProfileView.as_view(), name='superadmin-profile'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
