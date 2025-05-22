from django.db import models
from django.conf import settings

#Model to track user activities and system transactions
class ActivityLog(models.Model):

    class ActivityType(models.TextChoices):
        CREATE = 'create', 'Create'
        UPDATE = 'update', 'Update'
        DELETE = 'delete', 'Delete'
        LOGIN = 'login', 'Login'
        LOGOUT = 'logout', 'Logout'
        VIEW = 'view', 'View'
        SUSPEND = 'suspend', 'Suspend'
        ACTIVATE = 'activate', 'Activate'
        OTHER = 'other', 'Other'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='activities'
    )
    activity_type = models.CharField(max_length=20, choices=ActivityType.choices)
    object_type = models.CharField(max_length=100)  # Model name or table name
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Activity Log'
        verbose_name_plural = 'Activity Logs'

    def __str__(self):
        return f"{self.user.username if self.user else 'System'} - {self.activity_type} {self.object_type} at {self.timestamp}"

