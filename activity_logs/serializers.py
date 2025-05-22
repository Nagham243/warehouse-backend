from rest_framework import serializers
from .models import ActivityLog
from django.contrib.auth import get_user_model

User = get_user_model()

#Brief serializer for User in activity logs
class UserBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'user_type']

#Serializer for ActivityLog model
class ActivityLogSerializer(serializers.ModelSerializer):
    user = UserBriefSerializer(read_only=True)
    activity_type_display = serializers.CharField(source='get_activity_type_display', read_only=True)

    class Meta:
        model = ActivityLog
        fields = [
            'id', 'user', 'activity_type', 'activity_type_display',
            'object_type', 'timestamp'
        ]
        read_only_fields = fields