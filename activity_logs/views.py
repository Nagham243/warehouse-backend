from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response

from activity_logs.models import ActivityLog
from .serializers import ActivityLogSerializer
from accounts.permissions import IsSuperAdmin

#API endpoint for viewing activity logs
class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ActivityLog.objects.all().order_by('-timestamp')
    serializer_class = ActivityLogSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['user', 'activity_type', 'object_type']
    search_fields = ['user__username', 'details', 'ip_address']
    ordering_fields = ['timestamp', 'user', 'activity_type']

    #Get activities for a specific user
    @action(detail=False, methods=['get'])
    def user_activities(self, request):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({"error": "user_id parameter is required"}, status=400)

        activities = self.get_queryset().filter(user_id=user_id)
        page = self.paginate_queryset(activities)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(activities, many=True)
        return Response(serializer.data)

    #Get summary of activities by type
    @action(detail=False, methods=['get'])
    def activity_summary(self, request):
        from django.db.models import Count

        summary = ActivityLog.objects.values('activity_type').annotate(
            count=Count('id')
        ).order_by('-count')

        return Response(summary)
