from rest_framework import permissions

#Permission to only allow superadmins to access the view.
class IsSuperAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_superadmin

#Permission to only allow financial managers to access the view.
class IsFinancialManager(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_financial

#Permission to only allow technical support staff to access the view.
class IsTechnicalSupport(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_technical

#Permission to allow access to object owners or superadmins.
class IsOwnerOrSuperAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.is_superadmin or obj.id == request.user.id