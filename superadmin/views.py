from rest_framework import viewsets,permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.http import Http404
from itertools import chain
from django.contrib.auth import get_user_model
from django.db.models import Q , Count
from django.utils import timezone
from accounts.models import VendorProfile, VendorClassification,User
from accounts.serializers import (
    UserListSerializer, UserDetailSerializer,
    UserCreateSerializer, UserUpdateSerializer,
    UserStatusUpdateSerializer,VendorProfileSerializer,
    VendorVerificationSerializer
)
from accounts.permissions import IsSuperAdmin, IsOwnerOrSuperAdmin
from activity_logs.utils import log_activity
from django.core.exceptions import ValidationError
from .models import Category, SubCategory,Deal, Offer, DealStatus,VendorTypeCommission, TimePeriodCommission, OfferTypeCommission,CommissionType
from .serializers import (
    CategorySerializer,
    CategoryDetailSerializer,
    SubCategorySerializer,
    SubCategoryDetailSerializer,DealSerializer, DealDetailSerializer, DealUpdateSerializer,
    DealStatusUpdateSerializer, OfferSerializer, OfferDetailSerializer,
    OfferUpdateSerializer,VendorTypeCommissionSerializer, TimePeriodCommissionSerializer,
    OfferTypeCommissionSerializer, CommissionListSerializer
)
from .views_stats import UserStatsViewMixin
from django.middleware.csrf import get_token
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
import logging
logger = logging.getLogger(__name__)
from rest_framework import serializers
from datetime import timedelta


User = get_user_model()

class UserManagementViewSet(UserStatsViewMixin, viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-date_joined')
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['user_type', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['username', 'date_joined', 'user_type', 'last_login']


    def get_serializer_class(self):
        if self.action == 'list':
            return UserListSerializer
        elif self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        elif self.action in ['suspend', 'activate']:
            return UserStatusUpdateSerializer
        return UserDetailSerializer

    def get_permissions(self):
        if self.action in ['retrieve', 'update', 'partial_update']:
            self.permission_classes = [IsAuthenticated, IsOwnerOrSuperAdmin]
        else:
            self.permission_classes = [IsAuthenticated, IsSuperAdmin]
        return super().get_permissions()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        user_type = request.query_params.get('user_type', None)

        if user_type:
            queryset = queryset.filter(user_type=user_type)

        search = request.query_params.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )

        queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        """Create a new user and log activity"""
        user = serializer.save()
        log_activity(
            user=self.request.user,
            activity_type='create',
            object_type='User',
            details={'user_type': user.user_type},
        )

    def perform_update(self, serializer):
        """Update user and log activity"""
        instance = serializer.instance
        original_data = {
            'user_type': instance.user_type,
            'is_active': instance.is_active
        }

        user = serializer.save()

        log_activity(
            user=self.request.user,
            activity_type='update',
            object_type='User',
            details={
                'original': original_data,
                'updated': {
                    'user_type': user.user_type,
                    'is_active': user.is_active
                }
            },
        )

    def perform_destroy(self, instance):
        """Delete user and log activity"""
        user_id = instance.id
        user_type = instance.user_type

        instance.delete()

        log_activity(
            user=self.request.user,
            activity_type='delete',
            object_type='User',
            details={'user_type': user_type},
        )

    @action(detail=True, methods=['post'])
    def suspend(self, request, pk=None):
        try:
            user = self.get_object()
            serializer = self.get_serializer(data=request.data)

            serializer.is_valid(raise_exception=True)

            if serializer.validated_data['is_active'] is True:
                return Response(
                    {"error": "This endpoint is for suspending users only. Set is_active to false."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if user.id == request.user.id:
                return Response(
                    {"error": "You cannot suspend yourself."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user.is_active = False
            user.save()

            log_activity(
                user=request.user,
                activity_type='suspend',
                object_type='User',
                details={'user_type': user.user_type},
            )

            return Response({"success": "User suspended successfully"}, status=status.HTTP_200_OK)

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({"error": str(e)}, status=500)


    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a suspended user"""
        user = self.get_object()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            if serializer.validated_data['is_active'] is False:
                return Response(
                    {"error": "This endpoint is for activating users only. Set is_active to true."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user.is_active = True
            user.save()

            log_activity(
                user=request.user,
                activity_type='activate',
                object_type='User',
                details={'user_type': user.user_type},
            )

            return Response({"success": "User activated successfully"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def financial_managers(self, request):
        """List only financial managers"""
        queryset = self.get_queryset().filter(user_type='financial')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def technical_support(self, request):
        """List only technical support staff"""
        queryset = self.get_queryset().filter(user_type='technical')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def clients(self, request):
        """List only clients"""
        queryset = self.get_queryset().filter(user_type='client')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def vendors(self, request):
        """List only vendors"""
        queryset = self.get_queryset().filter(user_type='vendor')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def growth_stats(self, request):
        """Return user growth statistics for the last 30 days"""
        from django.db.models.functions import TruncDate
        from django.db.models import Count

        # Calculate date range
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)

        # Query for new users per day
        growth_data = (
            User.objects
            .filter(date_joined__date__gte=start_date, date_joined__date__lte=end_date)
            .annotate(date=TruncDate('date_joined'))
            .values('date')
            .annotate(count=Count('id'))
            .order_by('date')
        )

        # Convert to a dictionary for easier lookup
        growth_dict = {item['date'].isoformat(): item['count'] for item in growth_data}

        # Generate complete date range with counts (including days with 0 new users)
        complete_data = []
        current_date = start_date

        while current_date <= end_date:
            date_str = current_date.isoformat()
            complete_data.append({
                'date': date_str,
                'count': growth_dict.get(date_str, 0)
            })
            current_date += timedelta(days=1)

        return Response({
            'growthData': complete_data,
            'total': User.objects.count(),
            'active': User.objects.filter(is_active=True).count(),
        })


class CategoryManagementViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing product categories and subcategories
    Only superadmin has access to create, update and delete categories
    """
    queryset = Category.objects.all().order_by('name')
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']

    def get_serializer_class(self):
        if self.action in ['retrieve', 'subcategories']:
            return CategoryDetailSerializer
        return CategorySerializer

    def perform_create(self, serializer):
        """Create a new category and log activity"""
        category = serializer.save()
        log_activity(
            user=self.request.user,
            activity_type='create',
            object_type='Category',
            details={'category_name': category.name},
        )

    def perform_update(self, serializer):
        """Update category and log activity"""
        instance = serializer.instance
        original_data = {
            'name': instance.name,
            'description': instance.description,
        }

        category = serializer.save()

        log_activity(
            user=self.request.user,
            activity_type='update',
            object_type='Category',
            details={
                'original': original_data,
                'updated': {
                    'name': category.name,
                    'description': category.description,
                }
            },
        )

    def perform_destroy(self, instance):
        """Delete category and log activity"""
        category_name = instance.name

        if instance.subcategories.exists():
            raise ValidationError("Cannot delete category with existing subcategories")

        '''validation for active offers'''
        # from products.models import Product
        # if Product.objects.filter(category=instance, is_active=True).exists():
        #     raise ValidationError("Cannot delete category with active offers. Please deactivate related offers first.")

        instance.delete()

        log_activity(
            user=self.request.user,
            activity_type='delete',
            object_type='Category',
            details={'category_name': category_name},
        )

    @action(detail=True, methods=['get'])
    def subcategories(self, request, pk=None):
        """List all subcategories for a specific category"""
        category = self.get_object()
        subcategories = category.subcategories.all()
        serializer = SubCategorySerializer(subcategories, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_subcategory(self, request, pk=None):
        """Add a subcategory to a specific category"""
        category = self.get_object()
        serializer = SubCategorySerializer(data=request.data)

        if serializer.is_valid():
            subcategory = serializer.save(category=category)

            log_activity(
                user=request.user,
                activity_type='create',
                object_type='SubCategory',
                details={
                    'category_name': category.name,
                    'subcategory_name': subcategory.name
                },
            )

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def with_subcategory_count(self, request):
        """List all categories with the count of subcategories"""
        categories = self.get_queryset().annotate(subcategory_count=Count('subcategories'))
        serializer = CategorySerializer(categories, many=True)

        data = serializer.data
        for i, category in enumerate(categories):
            data[i]['subcategory_count'] = category.subcategory_count

        return Response(data)


class SubCategoryManagementViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing product subcategories
    Only superadmin has access to create, update and delete subcategories
    """
    queryset = SubCategory.objects.all().order_by('name')
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return SubCategoryDetailSerializer
        return SubCategorySerializer

    def perform_create(self, serializer):
        subcategory = serializer.save()
        log_activity(
            user=self.request.user,
            activity_type='create',
            object_type='SubCategory',
            details={
                'category_name': subcategory.category.name,
                'subcategory_name': subcategory.name
            },
        )

    def perform_update(self, serializer):
        instance = serializer.instance
        original_data = {
            'name': instance.name,
            'description': instance.description,
            'category': instance.category.id
        }

        subcategory = serializer.save()

        log_activity(
            user=self.request.user,
            activity_type='update',
            object_type='SubCategory',
            details={
                'original': original_data,
                'updated': {
                    'name': subcategory.name,
                    'description': subcategory.description,
                    'category': subcategory.category.id
                }
            },
        )

    def perform_destroy(self, instance):
        subcategory_name = instance.name
        category_name = instance.category.name

        '''validation for active offers'''
        # from products.models import Product
        # if Product.objects.filter(subcategory=instance, is_active=True).exists():
        #     raise ValidationError("Cannot delete subcategory with active offers. Please deactivate related offers first.")

        instance.delete()

        log_activity(
            user=self.request.user,
            activity_type='delete',
            object_type='SubCategory',
            details={
                'category_name': category_name,
                'subcategory_name': subcategory_name
            },
        )

    @action(detail=True, methods=['post'])
    def change_category(self, request, pk=None):
        """Change the parent category of a subcategory"""
        subcategory = self.get_object()

        if 'category_id' not in request.data:
            return Response(
                {"error": "category_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            new_category = Category.objects.get(id=request.data['category_id'])
        except Category.DoesNotExist:
            return Response(
                {"error": "Category not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        original_category = subcategory.category

        subcategory.category = new_category
        subcategory.save()

        log_activity(
            user=request.user,
            activity_type='update',
            object_type='SubCategory',
            details={
                'subcategory_name': subcategory.name,
                'original_category': original_category.name,
                'new_category': new_category.name
            },
        )

        serializer = self.get_serializer(subcategory)
        return Response(serializer.data)

class VendorManagementViewSet(viewsets.ModelViewSet):
    """
    Viewset for managing vendor profiles by superadmin
    """
    queryset = VendorProfile.objects.all().order_by('-created_at')
    serializer_class = VendorProfileSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]
    filterset_fields = [
        'is_verified',
        'classification'
    ]
    search_fields = [
        'business_name',
        'business_registration_number',
        'user__username',
        'user__email'
    ]
    ordering_fields = [
        'created_at',
        'business_name',
        'classification'
    ]

    @action(detail=True, methods=['POST'], serializer_class=VendorVerificationSerializer)
    def verify(self, request, pk=None):
        """
        Verify a vendor profile and optionally change classification
        """
        vendor_profile = self.get_object()
        serializer = self.get_serializer(
            vendor_profile,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            original_data = {
                'is_verified': vendor_profile.is_verified,
                'classification': vendor_profile.classification
            }

            updated_profile = serializer.save()

            log_activity(
                user=request.user,
                activity_type='update',
                object_type='Vendor',
                details={
                    'business_name': updated_profile.business_name,
                    'original': original_data,
                    'updated': {
                        'is_verified': updated_profile.is_verified,
                        'classification': updated_profile.classification
                    }
                },
            )

            return Response(
                VendorProfileSerializer(updated_profile).data,
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['GET'])
    def classification_summary(self, request):
        """
        Get summary of vendors by classification
        """
        summary = []
        for classification, _ in VendorClassification.choices:
            count = self.get_queryset().filter(classification=classification).count()
            summary.append({
                'classification': classification,
                'count': count
            })

        return Response(summary)

    @action(detail=False, methods=['GET'])
    def unverified_vendors(self, request):
        """
        List all unverified vendors
        """
        unverified = self.get_queryset().filter(is_verified=False)
        serializer = self.get_serializer(unverified, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['POST'])
    def change_classification(self, request, pk=None):
        """
        Change vendor classification
        """
        vendor_profile = self.get_object()

        new_classification = request.data.get('classification')
        if new_classification not in dict(VendorClassification.choices):
            return Response(
                {'error': 'Invalid classification'},
                status=status.HTTP_400_BAD_REQUEST
            )

        original_classification = vendor_profile.classification

        vendor_profile.classification = new_classification
        vendor_profile.save()

        log_activity(
            user=request.user,
            activity_type='update',
            object_type='Vendor',
            details={
                'business_name': vendor_profile.business_name,
                'original_classification': original_classification,
                'new_classification': new_classification
            }
        )

        serializer = self.get_serializer(vendor_profile)
        return Response(serializer.data)

    @action(detail=True, methods=['POST'])
    def update_working_hours(self, request, pk=None):
        """
        Update vendor's working hours
        """
        vendor_profile = self.get_object()

        working_hours = request.data.get('working_hours')
        if not isinstance(working_hours, dict):
            return Response(
                {'error': 'Working hours must be a valid JSON object'},
                status=status.HTTP_400_BAD_REQUEST
            )

        original_working_hours = vendor_profile.working_hours

        vendor_profile.working_hours = working_hours
        vendor_profile.save()

        log_activity(
            user=request.user,
            activity_type='update',
            object_type='Vendor',
            details={
                'business_name': vendor_profile.business_name,
                'original_working_hours': original_working_hours,
                'new_working_hours': working_hours
            }
        )

        serializer = self.get_serializer(vendor_profile)
        return Response(serializer.data)

    @action(detail=True, methods=['POST'])
    def update_branches(self, request, pk=None):
        """
        Update vendor's branches
        """
        vendor_profile = self.get_object()

        branches = request.data.get('branches')
        if not isinstance(branches, list):
            return Response(
                {'error': 'Branches must be a valid JSON array'},
                status=status.HTTP_400_BAD_REQUEST
            )

        original_branches = vendor_profile.branches

        vendor_profile.branches = branches
        vendor_profile.save()

        log_activity(
            user=request.user,
            activity_type='update',
            object_type='Vendor',
            details={
                'business_name': vendor_profile.business_name,
                'original_branches': original_branches,
                'new_branches': branches
            }
        )

        serializer = self.get_serializer(vendor_profile)
        return Response(serializer.data)

    @action(detail=False, methods=['GET'])
    def classification_choices(self, request):
        """Get available classification choices"""
        return Response(dict(VendorClassification.choices))

class DealManagementViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing deals between clients and vendors.
    Only superadmin can access these endpoints to review, accept, reject, and edit deals.
    """
    queryset = Deal.objects.all().order_by('-created_at')
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'category', 'is_active', 'is_featured']
    search_fields = ['title', 'description', 'client__username', 'vendor__username']
    ordering_fields = ['created_at', 'amount', 'status', 'updated_at']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return DealDetailSerializer
        elif self.action in ['update', 'partial_update']:
            return DealUpdateSerializer
        elif self.action in ['approve', 'reject']:
            return DealStatusUpdateSerializer
        return DealSerializer

    def perform_create(self, serializer):
        """Create a new deal and log activity"""
        deal = serializer.save()
        log_activity(
            user=self.request.user,
            activity_type='create',
            object_type='Deal',
            details={'deal_title': deal.title},
        )

    def perform_update(self, serializer):
        """Update deal and log activity"""
        instance = serializer.instance
        original_data = {
            'title': instance.title,
            'description': instance.description,
            'status': instance.status,
            'is_active': instance.is_active
        }

        deal = serializer.save()

        log_activity(
            user=self.request.user,
            activity_type='update',
            object_type='Deal',
            details={
                'deal_title': deal.title,
                'original': original_data,
                'updated': {
                    'title': deal.title,
                    'description': deal.description,
                    'status': deal.status,
                    'is_active': deal.is_active
                }
            },
        )

    def perform_destroy(self, instance):
        """Delete deal and log activity"""
        deal_title = instance.title
        instance.delete()

        log_activity(
            user=self.request.user,
            activity_type='delete',
            object_type='Deal',
            details={'deal_title': deal_title},
        )

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a pending deal"""
        deal = self.get_object()

        if deal.status != DealStatus.PENDING:
            return Response(
                {"error": f"Cannot approve a deal with status '{deal.get_status_display()}'"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(deal, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.validated_data['status'] = DealStatus.APPROVED
            serializer.validated_data['approved_at'] = timezone.now()
            serializer.validated_data['reviewed_by'] = request.user

            deal = serializer.save()
            log_activity(
                user=self.request.user,
                activity_type='approve',
                object_type='Deal',
                details={
                    'deal_title': deal.title,
                    'admin_notes': deal.admin_notes
                },
            )

            return Response(DealDetailSerializer(deal).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a pending deal"""
        deal = self.get_object()

        if deal.status != DealStatus.PENDING:
            return Response(
                {"error": f"Cannot reject a deal with status '{deal.get_status_display()}'"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if 'rejection_reason' not in request.data or not request.data['rejection_reason'].strip():
            return Response(
                {"error": "Rejection reason is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(deal, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.validated_data['status'] = DealStatus.REJECTED
            serializer.validated_data['rejected_at'] = timezone.now()
            serializer.validated_data['reviewed_by'] = request.user

            deal = serializer.save()
            log_activity(
                user=self.request.user,
                activity_type='reject',
                object_type='Deal',
                details={
                    'deal_title': deal.title,
                    'rejection_reason': deal.rejection_reason
                },
            )

            return Response(DealDetailSerializer(deal).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def pending_deals(self, request):
        """List all pending deals"""
        queryset = self.get_queryset().filter(status=DealStatus.PENDING)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def approved_deals(self, request):
        """List all approved deals"""
        queryset = self.get_queryset().filter(status=DealStatus.APPROVED)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def rejected_deals(self, request):
        """List all rejected deals"""
        queryset = self.get_queryset().filter(status=DealStatus.REJECTED)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class OfferManagementViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing vendor offers.
    Only superadmin can access these endpoints to review and manage offers.
    """
    queryset = Offer.objects.all().order_by('-created_at')
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_approved', 'is_active', 'has_violation', 'category']
    search_fields = ['title', 'description', 'vendor__username']
    ordering_fields = ['created_at', 'price', 'updated_at']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return OfferDetailSerializer
        elif self.action in ['update', 'partial_update', 'flag_violation', 'clear_violation']:
            return OfferUpdateSerializer
        return OfferSerializer

    def perform_create(self, serializer):
        """Create a new offer and log activity"""
        offer = serializer.save()
        log_activity(
            user=self.request.user,
            activity_type='create',
            object_type='Offer',
            details={'offer_title': offer.title},
        )

    def perform_update(self, serializer):
        """Update offer and log activity"""
        instance = serializer.instance
        original_data = {
            'title': instance.title,
            'description': instance.description,
            'is_approved': instance.is_approved,
            'is_active': instance.is_active,
            'has_violation': instance.has_violation
        }

        offer = serializer.save()

        log_activity(
            user=self.request.user,
            activity_type='update',
            object_type='Offer',
            details={
                'offer_title': offer.title,
                'original': original_data,
                'updated': {
                    'title': offer.title,
                    'description': offer.description,
                    'is_approved': offer.is_approved,
                    'is_active': offer.is_active,
                    'has_violation': offer.has_violation
                }
            },
        )

    def perform_destroy(self, instance):
        """Delete offer and log activity"""
        offer_title = instance.title
        instance.delete()

        log_activity(
            user=self.request.user,
            activity_type='delete',
            object_type='Offer',
            details={'offer_title': offer_title},
        )

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a vendor offer"""
        offer = self.get_object()

        if offer.is_approved:
            return Response(
                {"error": "Offer is already approved"},
                status=status.HTTP_400_BAD_REQUEST
            )

        offer.is_approved = True
        offer.reviewed_by = request.user
        offer.rejection_reason = None
        offer.save()

        log_activity(
            user=self.request.user,
            activity_type='approve',
            object_type='Offer',
            details={'offer_title': offer.title},
        )

        return Response(OfferSerializer(offer).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a vendor offer"""
        offer = self.get_object()

        if 'rejection_reason' not in request.data or not request.data['rejection_reason'].strip():
            return Response(
                {"error": "Rejection reason is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        offer.is_approved = False
        offer.reviewed_by = request.user
        offer.rejection_reason = request.data['rejection_reason']
        offer.save()

        log_activity(
            user=self.request.user,
            activity_type='reject',
            object_type='Offer',
            details={
                'offer_title': offer.title,
                'rejection_reason': offer.rejection_reason
            },
        )

        return Response(OfferSerializer(offer).data)

    @action(detail=True, methods=['post'])
    def flag_violation(self, request, pk=None):
        """Flag an offer as violating policies"""
        offer = self.get_object()

        if 'violation_notes' not in request.data or not request.data['violation_notes'].strip():
            return Response(
                {"error": "Violation notes are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        offer.has_violation = True
        offer.violation_notes = request.data['violation_notes']
        offer.is_active = False
        offer.reviewed_by = request.user
        offer.save()

        log_activity(
            user=self.request.user,
            activity_type='violation',
            object_type='Offer',
            details={
                'offer_title': offer.title,
                'violation_notes': offer.violation_notes
            },
        )

        return Response(OfferSerializer(offer).data)

    @action(detail=True, methods=['post'])
    def clear_violation(self, request, pk=None):
        """Clear the violation flag from an offer"""
        offer = self.get_object()

        if not offer.has_violation:
            return Response(
                {"error": "Offer has no violation flag to clear"},
                status=status.HTTP_400_BAD_REQUEST
            )

        offer.has_violation = False
        offer.violation_notes = None
        offer.reviewed_by = request.user
        offer.save()

        log_activity(
            user=self.request.user,
            activity_type='clear_violation',
            object_type='Offer',
            details={'offer_title': offer.title},
        )

        return Response(OfferSerializer(offer).data)

    @action(detail=False, methods=['get'])
    def pending_approval(self, request):
        """List all offers pending approval"""
        queryset = self.get_queryset().filter(is_approved=False,
                                              rejection_reason__isnull=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def violations(self, request):
        """List all offers with policy violations"""
        queryset = self.get_queryset().filter(has_violation=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class CommissionManagementViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing commissions (pricing and commission management).
    """
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'commission_type']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'updated_at', 'percentage', 'name']
    ordering = ['-created_at']

    def get_permissions(self):
        """
        Only superadmins and financial managers can manage commissions
        """
        return [permissions.IsAuthenticated()]

    def check_permissions(self, request):
        """
        Check if user has superadmin or financial user type permissions
        """
        try:
            super().check_permissions(request)
            user = request.user

            is_superadmin = False
            is_financial = False

            if hasattr(user, 'is_superadmin'):
                is_superadmin = user.is_superadmin
            elif hasattr(user, 'user_type'):
                is_superadmin = user.user_type == 'superadmin'

            if hasattr(user, 'is_financial'):
                is_financial = user.is_financial
            elif hasattr(user, 'user_type'):
                is_financial = user.user_type == 'financial'

            if not (is_superadmin or is_financial):
                if user.is_staff or user.is_superuser:
                    return True

                self.permission_denied(
                    request,
                    message="You do not have permission to manage commissions."
                )

        except Exception as e:
            logger.error(f"Permission check error: {str(e)}")
            self.permission_denied(
                request,
                message="Permission check failed. Please contact support."
            )

    def get_serializer_class(self):
        """
        Return appropriate serializer based on action and commission_type
        """
        try:
            commission_type = self.request.query_params.get('commission_type')

            if self.action == 'list':
                return CommissionListSerializer

            if self.action in ['create', 'update', 'partial_update']:
                if commission_type == CommissionType.VENDOR_TYPE:
                    return VendorTypeCommissionSerializer
                elif commission_type == CommissionType.TIME_PERIOD:
                    return TimePeriodCommissionSerializer
                elif commission_type == CommissionType.OFFER_TYPE:
                    return OfferTypeCommissionSerializer

                if hasattr(self.request, 'data') and 'commission_type' in self.request.data:
                    commission_type = self.request.data.get('commission_type')
                    if commission_type == CommissionType.VENDOR_TYPE:
                        return VendorTypeCommissionSerializer
                    elif commission_type == CommissionType.TIME_PERIOD:
                        return TimePeriodCommissionSerializer
                    elif commission_type == CommissionType.OFFER_TYPE:
                        return OfferTypeCommissionSerializer

            if self.action != 'list':
                try:
                    instance = self.get_object()
                    if isinstance(instance, VendorTypeCommission):
                        return VendorTypeCommissionSerializer
                    elif isinstance(instance, TimePeriodCommission):
                        return TimePeriodCommissionSerializer
                    elif isinstance(instance, OfferTypeCommission):
                        return OfferTypeCommissionSerializer
                except Exception as e:
                    logger.error(f"Error getting object for serializer: {str(e)}")

            return VendorTypeCommissionSerializer

        except Exception as e:
            logger.error(f"Error in get_serializer_class: {str(e)}")
            return VendorTypeCommissionSerializer

    def get_queryset(self):
        """
        Return queryset based on commission type
        """
        try:
            commission_type = self.request.query_params.get('commission_type')
            is_active = self.request.query_params.get('is_active')

            if commission_type == CommissionType.VENDOR_TYPE:
                queryset = VendorTypeCommission.objects.all()
            elif commission_type == CommissionType.TIME_PERIOD:
                queryset = TimePeriodCommission.objects.all()
            elif commission_type == CommissionType.OFFER_TYPE:
                queryset = OfferTypeCommission.objects.all()
            else:
                queryset = VendorTypeCommission.objects.all()

            logger.debug(f"Commission type: {commission_type}, queryset model: {queryset.model.__name__}")

            if is_active is not None:
                try:
                    is_active_bool = is_active.lower() == 'true'
                    queryset = queryset.filter(is_active=is_active_bool)
                except Exception as e:
                    logger.error(f"Error filtering by is_active: {str(e)}")

            return queryset

        except Exception as e:
            logger.error(f"Error in get_queryset: {str(e)}")
            from django.db.models import Q
            return VendorTypeCommission.objects.filter(Q(pk=None))

    def get_object(self):
        """
        Get the specific commission object based on ID and type
        """
        try:
            lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
            if lookup_url_kwarg not in self.kwargs:
                return None

            lookup = self.kwargs[lookup_url_kwarg]
            commission_type = self.request.query_params.get('commission_type')

            logger.debug(f"Looking up commission with ID: {lookup}, type: {commission_type}")

            if commission_type == CommissionType.VENDOR_TYPE:
                return VendorTypeCommission.objects.get(pk=lookup)
            elif commission_type == CommissionType.TIME_PERIOD:
                return TimePeriodCommission.objects.get(pk=lookup)
            elif commission_type == CommissionType.OFFER_TYPE:
                return OfferTypeCommission.objects.get(pk=lookup)

            try:
                return VendorTypeCommission.objects.get(pk=lookup)
            except VendorTypeCommission.DoesNotExist:
                try:
                    return TimePeriodCommission.objects.get(pk=lookup)
                except TimePeriodCommission.DoesNotExist:
                    try:
                        return OfferTypeCommission.objects.get(pk=lookup)
                    except OfferTypeCommission.DoesNotExist:
                        raise Http404(f"Commission with ID {lookup} not found")

        except (VendorTypeCommission.DoesNotExist,
                TimePeriodCommission.DoesNotExist,
                OfferTypeCommission.DoesNotExist) as e:
            logger.warning(f"Commission lookup error: {str(e)}")
            raise Http404(f"Commission with ID {lookup} not found")
        except Exception as e:
            logger.error(f"Unexpected error in get_object: {str(e)}")
            raise Http404("Error retrieving commission")

    def perform_create(self, serializer):
        """Set created_by and updated_by fields"""
        try:
            serializer.save(created_by=self.request.user, updated_by=self.request.user)
        except Exception as e:
            logger.error(f"Error in perform_create: {str(e)}")
            raise serializers.ValidationError(f"Failed to create commission: {str(e)}")

    def perform_update(self, serializer):
        """Update the updated_by field"""
        print(f"User: {request.user}")
        print(f"User permissions: {request.user.get_all_permissions()}")
        print(f"Request data: {request.data}")
        return super().update(request, *args, **kwargs)
        try:
            serializer.save(updated_by=self.request.user)
        except Exception as e:
            logger.error(f"Error in perform_update: {str(e)}")
            raise serializers.ValidationError(f"Failed to update commission: {str(e)}")

    def create(self, request, *args, **kwargs):
        """
        Create a new commission record based on commission_type
        """
        try:
            commission_type = request.data.get('commission_type')

            if not commission_type:
                return Response(
                    {"error": "commission_type is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer_class = self.get_serializer_class()
            serializer = serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)

            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except Exception as e:
            logger.error(f"Error in create: {str(e)}")
            return Response(
                {"error": f"Failed to create commission: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Return a summary of active commissions for each type
        """
        try:
            vendor_type_count = VendorTypeCommission.objects.filter(is_active=True).count()
            time_period_count = TimePeriodCommission.objects.filter(is_active=True).count()
            offer_type_count = OfferTypeCommission.objects.filter(is_active=True).count()

            return Response({
                'vendor_type_commissions': vendor_type_count,
                'time_period_commissions': time_period_count,
                'offer_type_commissions': offer_type_count,
                'total_active_commissions': vendor_type_count + time_period_count + offer_type_count
            })
        except Exception as e:
            logger.error(f"Error in commission summary: {str(e)}")
            return Response(
                {"error": "Failed to retrieve commission summary"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def vendor_commissions(self, request):
        """
        Returns all vendors with their classifications and applicable commissions
        """
        try:
            # Get all vendors
            vendors = User.objects.filter(user_type=User.UserType.VENDOR)

            # Get all active vendor type commissions
            commissions = VendorTypeCommission.objects.filter(is_active=True)

            # Build vendor commission data
            vendor_data = []
            for vendor in vendors:
                # Get vendor profile if exists
                vendor_profile = None
                try:
                    vendor_profile = vendor.vendor_profile
                    classification = vendor_profile.classification
                except (AttributeError, VendorProfile.DoesNotExist):
                    classification = None

                # Find applicable commission
                applicable_commission = None
                if classification:
                    try:
                        applicable_commission = commissions.get(vendor_classification=classification)
                    except VendorTypeCommission.DoesNotExist:
                        pass

                vendor_data.append({
                    'id': vendor.id,
                    'username': vendor.username,
                    'full_name': f"{vendor.first_name} {vendor.last_name}".strip(),
                    'business_name': vendor_profile.business_name if vendor_profile else None,
                    'classification': classification,
                    'commission': {
                        'id': applicable_commission.id if applicable_commission else None,
                        'name': applicable_commission.name if applicable_commission else None,
                        'percentage': applicable_commission.percentage if applicable_commission else None
                    } if applicable_commission else None
                })

            return Response(vendor_data)
        except Exception as e:
            logger.error(f"Error in vendor_commissions: {str(e)}")
            return Response(
                {"error": f"Failed to retrieve vendor commissions: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def assign_commission(self, request, pk=None):
        """
        Assign a specific commission to a vendor
        If commission is not based on existing classifications, mark vendor as special
        """
        try:
            # Get the vendor
            vendor = User.objects.get(pk=pk, user_type=User.UserType.VENDOR)

            # Get vendor profile or create one if it doesn't exist
            try:
                vendor_profile = vendor.vendor_profile
            except VendorProfile.DoesNotExist:
                vendor_profile = VendorProfile.objects.create(
                    user=vendor,
                    business_name=f"{vendor.first_name} {vendor.last_name}".strip() or vendor.username,
                    business_registration_number=f"AUTO-{vendor.id}"  # Placeholder value
                )

            # Get the commission ID from request
            commission_id = request.data.get('commission_id')
            if not commission_id:
                return Response(
                    {"error": "commission_id is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                commission = VendorTypeCommission.objects.get(pk=commission_id, is_active=True)
            except VendorTypeCommission.DoesNotExist:
                return Response(
                    {"error": f"Commission with ID {commission_id} not found or not active"},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Check if commission is for a standard classification or custom
            standard_classifications = [
                VendorClassification.BRONZE,
                VendorClassification.SILVER,
                VendorClassification.GOLD,
                VendorClassification.PLATINUM
            ]

            if commission.vendor_classification in standard_classifications:
                # If standard classification, update vendor profile
                vendor_profile.classification = commission.vendor_classification
            else:
                # If custom classification or not matching standard, mark as special
                vendor_profile.classification = VendorClassification.SPECIAL

            vendor_profile.save()

            return Response({
                'vendor_id': vendor.id,
                'vendor_name': vendor.username,
                'classification': vendor_profile.classification,
                'commission': {
                    'id': commission.id,
                    'name': commission.name,
                    'percentage': commission.percentage
                }
            })

        except User.DoesNotExist:
            return Response(
                {"error": f"Vendor with ID {pk} not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error in assign_commission: {str(e)}")
            return Response(
                {"error": f"Failed to assign commission: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def create_special_commission(self, request):
        """
        Create a special commission for a vendor and mark them as having special classification
        """
        try:
            vendor_id = request.data.get('vendor_id')
            if not vendor_id:
                return Response(
                    {"error": "vendor_id is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get the vendor
            try:
                vendor = User.objects.get(pk=vendor_id, user_type=User.UserType.VENDOR)
            except User.DoesNotExist:
                return Response(
                    {"error": f"Vendor with ID {vendor_id} not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Get or create vendor profile
            try:
                vendor_profile = vendor.vendor_profile
            except VendorProfile.DoesNotExist:
                vendor_profile = VendorProfile.objects.create(
                    user=vendor,
                    business_name=f"{vendor.first_name} {vendor.last_name}".strip() or vendor.username,
                    business_registration_number=f"AUTO-{vendor.id}"  # Placeholder
                )

            # Create commission data
            commission_data = {
                'name': request.data.get('name', f"Special commission for {vendor.username}"),
                'description': request.data.get('description', f"Custom commission rate for {vendor.username}"),
                'percentage': request.data.get('percentage'),
                'commission_type': CommissionType.VENDOR_TYPE,
                'vendor_classification': 'special',
                'is_active': True
            }

            # Validate percentage
            if not commission_data['percentage']:
                return Response(
                    {"error": "percentage is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Create the commission
            serializer = VendorTypeCommissionSerializer(data=commission_data)
            serializer.is_valid(raise_exception=True)
            commission = serializer.save(created_by=request.user, updated_by=request.user)

            # Update vendor to special classification
            vendor_profile.classification = VendorClassification.SPECIAL
            vendor_profile.save()

            return Response({
                'commission': serializer.data,
                'vendor': {
                    'id': vendor.id,
                    'username': vendor.username,
                    'classification': vendor_profile.classification
                }
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error in create_special_commission: {str(e)}")
            return Response(
                {"error": f"Failed to create special commission: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='vendor-counts')
    def vendor_counts(self, request):
        """
        Return counts of vendors in each classification
        """
        try:
            from django.db.models import Count
            from accounts.models import VendorProfile

            counts = VendorProfile.objects.values('classification').annotate(
                count=Count('classification')
            ).order_by('classification')

            result = {
                'bronze': 0,
                'silver': 0,
                'gold': 0,
                'platinum': 0,
                'special': 0
            }

            for item in counts:
                classification = item['classification'].lower()  # Ensure case matches
                if classification in result:
                    result[classification] = item['count']

            return Response(result)
        except Exception as e:
            logger.error(f"Error in vendor_counts: {str(e)}")
            return Response(
                {"error": "Failed to retrieve vendor counts"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['GET'])
@permission_classes([AllowAny])
def check_auth_status(request):
    """
    Returns auth status without requiring authentication.
    Frontend can use this to verify session state.
    """
    if request.user.is_authenticated:
        return Response({
            'authenticated': True,
            'username': request.user.username,
            'csrfToken': get_token(request)
        })
    else:
        return Response({
            'authenticated': False
        }, status=200)  # Still return 200 but with authenticated: false

@api_view(['GET'])
@permission_classes([AllowAny])
def csrf_token(request):
    """Return a CSRF token that can be used by the frontend"""
    token = get_token(request)
    return JsonResponse({'csrfToken': token})
