from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, UserProfile

class UserProfileInline(admin.StackedInline):
    """Inline admin for UserProfile"""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'


class CustomUserAdmin(UserAdmin):
    """Custom admin for User model"""
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'phone_number')}),
        (_('User type'), {'fields': ('user_type',)}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type', 'is_active')
    list_filter = ('is_active', 'user_type', 'is_staff', 'is_superuser')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    inlines = (UserProfileInline,)


admin.site.register(User, CustomUserAdmin)

from django.contrib import admin
from activity_logs.models import ActivityLog

class ActivityLogAdmin(admin.ModelAdmin):
    """Admin for ActivityLog model"""
    list_display = ('user', 'activity_type', 'object_type', 'timestamp')
    list_filter = ('activity_type', 'object_type', 'timestamp')
    search_fields = ('user__username', 'object_type', 'object_id', 'ip_address')
    date_hierarchy = 'timestamp'
    readonly_fields = ('user', 'activity_type', 'object_type',  'timestamp')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

admin.site.register(ActivityLog, ActivityLogAdmin)
