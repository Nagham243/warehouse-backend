from rest_framework import serializers
from .models import Category, SubCategory,Deal, Offer, DealStatus,CommissionType, VendorTypeCommission,TimePeriodCommission, OfferTypeCommission
from accounts.serializers import UserListSerializer
import logging
logger = logging.getLogger(__name__)


class SubCategorySerializer(serializers.ModelSerializer):
    """
    Serializer for SubCategory model (for list/create operations)
    """
    class Meta:
        model = SubCategory
        fields = [
            'id', 'name', 'slug', 'description',
            'image', 'is_active', 'category',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']
        extra_kwargs = {
            'category': {'required': False}
        }

class SubCategoryDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for SubCategory (for retrieve operations)
    """
    category_name = serializers.ReadOnlyField(source='category.name')

    class Meta:
        model = SubCategory
        fields = [
            'id', 'name', 'slug', 'description',
            'image', 'is_active', 'category', 'category_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']

class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for Category model (for list/create operations)
    """
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description',
            'image', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']

class CategoryDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for Category model including subcategories (for retrieve operations)
    """
    subcategories = SubCategorySerializer(many=True, read_only=True)
    subcategory_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description',
            'image', 'is_active', 'created_at', 'updated_at',
            'subcategories', 'subcategory_count'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']

    def get_subcategory_count(self, obj):
        return obj.subcategories.count()

class OfferSerializer(serializers.ModelSerializer):
    """
    Serializer for vendor offers
    """
    vendor_name = serializers.ReadOnlyField(source='vendor.username')
    category_name = serializers.ReadOnlyField(source='category.name')
    subcategory_name = serializers.ReadOnlyField(source='subcategory.name')
    reviewed_by_name = serializers.ReadOnlyField(source='reviewed_by.username')

    class Meta:
        model = Offer
        fields = [
            'id', 'title', 'slug', 'description', 'vendor', 'vendor_name',
            'price', 'currency', 'category', 'category_name', 'subcategory',
            'subcategory_name', 'is_active', 'is_approved', 'reviewed_by',
            'reviewed_by_name', 'rejection_reason', 'created_at', 'updated_at',
            'expiry_date', 'has_violation', 'violation_notes'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']


class OfferDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for vendor offers
    """
    vendor = UserListSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    subcategory = SubCategorySerializer(read_only=True)
    reviewed_by = UserListSerializer(read_only=True)

    class Meta:
        model = Offer
        fields = [
            'id', 'title', 'slug', 'description', 'vendor',
            'price', 'currency', 'category', 'subcategory',
            'is_active', 'is_approved', 'reviewed_by',
            'rejection_reason', 'created_at', 'updated_at',
            'expiry_date', 'has_violation', 'violation_notes'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']


class DealSerializer(serializers.ModelSerializer):
    """
    Serializer for deals between clients and vendors
    """
    client_name = serializers.ReadOnlyField(source='client.username')
    vendor_name = serializers.ReadOnlyField(source='vendor.username')
    category_name = serializers.ReadOnlyField(source='category.name')
    subcategory_name = serializers.ReadOnlyField(source='subcategory.name')
    status_display = serializers.ReadOnlyField(source='get_status_display')
    reviewed_by_name = serializers.ReadOnlyField(source='reviewed_by.username')

    class Meta:
        model = Deal
        fields = [
            'id', 'title', 'slug', 'description', 'client', 'client_name',
            'vendor', 'vendor_name', 'amount', 'currency', 'category',
            'category_name', 'subcategory', 'subcategory_name', 'status',
            'status_display', 'reviewed_by', 'reviewed_by_name',
            'rejection_reason', 'admin_notes', 'terms', 'created_at',
            'updated_at', 'expiry_date', 'approved_at', 'rejected_at',
            'is_featured', 'is_active'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at',
                            'approved_at', 'rejected_at']


class DealDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for deals between clients and vendors
    """
    client = UserListSerializer(read_only=True)
    vendor = UserListSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    subcategory = SubCategorySerializer(read_only=True)
    status_display = serializers.ReadOnlyField(source='get_status_display')
    reviewed_by = UserListSerializer(read_only=True)

    class Meta:
        model = Deal
        fields = [
            'id', 'title', 'slug', 'description', 'client',
            'vendor', 'amount', 'currency', 'category',
            'subcategory', 'status', 'status_display', 'reviewed_by',
            'rejection_reason', 'admin_notes', 'terms', 'created_at',
            'updated_at', 'expiry_date', 'approved_at', 'rejected_at',
            'is_featured', 'is_active'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at',
                            'approved_at', 'rejected_at']


class DealUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating deals by admin
    """
    class Meta:
        model = Deal
        fields = [
            'title', 'description', 'amount', 'currency',
            'category', 'subcategory', 'admin_notes',
            'terms', 'is_featured', 'is_active', 'expiry_date'
        ]


class DealStatusUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating deal status by admin
    """
    class Meta:
        model = Deal
        fields = ['status', 'rejection_reason', 'admin_notes']

    def validate_status(self, value):
        """Validate status transitions"""
        if value not in dict(DealStatus.choices):
            raise serializers.ValidationError(f"Invalid status: {value}")
        return value


class OfferUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating offers by admin
    """
    class Meta:
        model = Offer
        fields = [
            'title', 'description', 'price', 'currency',
            'category', 'subcategory', 'is_active', 'is_approved',
            'rejection_reason', 'has_violation', 'violation_notes'
        ]

class VendorTypeCommissionSerializer(serializers.ModelSerializer):
    """Serializer for VendorTypeCommission model"""
    created_by_name = serializers.ReadOnlyField(source='created_by.username')
    updated_by_name = serializers.ReadOnlyField(source='updated_by.username')
    commission_type_display = serializers.ReadOnlyField(source='get_commission_type_display')
    vendor_classification_display = serializers.ReadOnlyField(source='get_vendor_classification_display')

    class Meta:
        model = VendorTypeCommission
        fields = [
            'id', 'name', 'description', 'commission_type',
            'commission_type_display', 'percentage', 'is_active',
            'vendor_classification', 'vendor_classification_display',
            'created_by', 'created_by_name', 'updated_by',
            'updated_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'updated_by', 'created_at', 'updated_at']

    def validate(self, attrs):
        """
        Check if there's already an active commission for this vendor classification
        """
        if self.instance:  # If updating
            if attrs.get('is_active', self.instance.is_active) and attrs.get('vendor_classification', self.instance.vendor_classification):
                active_commissions = VendorTypeCommission.objects.filter(
                    vendor_classification=attrs.get('vendor_classification', self.instance.vendor_classification),
                    is_active=True
                ).exclude(id=self.instance.id)
                if active_commissions.exists():
                    raise serializers.ValidationError(
                        f"An active commission already exists for {attrs['vendor_classification']} vendors."
                    )
        else:  # If creating
            if attrs.get('is_active'):
                active_commissions = VendorTypeCommission.objects.filter(
                    vendor_classification=attrs['vendor_classification'],
                    is_active=True
                )
                if active_commissions.exists():
                    raise serializers.ValidationError(
                        f"An active commission already exists for {attrs['vendor_classification']} vendors."
                    )

        # Set commission_type explicitly for VendorTypeCommission
        attrs['commission_type'] = CommissionType.VENDOR_TYPE
        return attrs


class TimePeriodCommissionSerializer(serializers.ModelSerializer):
    """Serializer for TimePeriodCommission model"""
    created_by_name = serializers.ReadOnlyField(source='created_by.username')
    updated_by_name = serializers.ReadOnlyField(source='updated_by.username')
    commission_type_display = serializers.ReadOnlyField(source='get_commission_type_display')

    class Meta:
        model = TimePeriodCommission
        fields = [
            'id', 'name', 'description', 'commission_type',
            'commission_type_display', 'percentage', 'is_active',
            'start_date', 'end_date', 'created_by', 'created_by_name',
            'updated_by', 'updated_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'updated_by', 'created_at', 'updated_at']

    def validate(self, attrs):
        """
        Validate that end_date is after start_date and check for overlapping periods
        """
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')

        if start_date and end_date and end_date <= start_date:
            raise serializers.ValidationError({"end_date": "End date must be after start date"})

        # Check overlapping periods only if this is an active commission
        if attrs.get('is_active', getattr(self.instance, 'is_active', True)):
            overlapping_query = TimePeriodCommission.objects.filter(
                is_active=True,
                start_date__lt=end_date,
                end_date__gt=start_date
            )

            # Exclude self if updating
            if self.instance:
                overlapping_query = overlapping_query.exclude(id=self.instance.id)

            if overlapping_query.exists():
                raise serializers.ValidationError(
                    "This time period overlaps with an existing active commission period."
                )

        # Set commission_type explicitly for TimePeriodCommission
        attrs['commission_type'] = CommissionType.TIME_PERIOD
        return attrs


class OfferTypeCommissionSerializer(serializers.ModelSerializer):
    """Serializer for OfferTypeCommission model"""
    created_by_name = serializers.ReadOnlyField(source='created_by.username')
    updated_by_name = serializers.ReadOnlyField(source='updated_by.username')
    commission_type_display = serializers.ReadOnlyField(source='get_commission_type_display')
    category_name = serializers.ReadOnlyField(source='category.name')
    subcategory_name = serializers.SerializerMethodField()

    class Meta:
        model = OfferTypeCommission
        fields = [
            'id', 'name', 'description', 'commission_type',
            'commission_type_display', 'percentage', 'is_active',
            'category', 'category_name', 'subcategory', 'subcategory_name',
            'created_by', 'created_by_name', 'updated_by',
            'updated_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'updated_by', 'created_at', 'updated_at']

    def get_subcategory_name(self, obj):
        return obj.subcategory.name if obj.subcategory else None

    def validate(self, attrs):
        """
        Check if category and subcategory match and if there's already an active
        commission for this category/subcategory combination
        """
        category = attrs.get('category')
        subcategory = attrs.get('subcategory')

        # Validate subcategory belongs to the selected category
        if subcategory and category and subcategory.category_id != category.id:
            raise serializers.ValidationError(
                {"subcategory": "Subcategory must belong to the selected category"}
            )

        # Check for existing active commissions with same category/subcategory
        if attrs.get('is_active', getattr(self.instance, 'is_active', True)):
            commission_filter = {
                'category': category or getattr(self.instance, 'category', None),
                'is_active': True
            }

            # Add subcategory to filter if provided
            if subcategory:
                commission_filter['subcategory'] = subcategory
            elif hasattr(self.instance, 'subcategory'):
                commission_filter['subcategory'] = self.instance.subcategory

            # Query for existing commissions
            existing_query = OfferTypeCommission.objects.filter(**commission_filter)

            # Exclude self if updating
            if self.instance:
                existing_query = existing_query.exclude(id=self.instance.id)

            if existing_query.exists():
                category_name = category.name if category else self.instance.category.name
                subcategory_name = subcategory.name if subcategory else (
                    self.instance.subcategory.name if self.instance and self.instance.subcategory else "All subcategories"
                )
                raise serializers.ValidationError(
                    f"An active commission already exists for category '{category_name}' "
                    f"and subcategory '{subcategory_name}'."
                )

        # Set commission_type explicitly for OfferTypeCommission
        attrs['commission_type'] = CommissionType.OFFER_TYPE
        return attrs


# Combined serializer for listing all commission types
class CommissionListSerializer(serializers.Serializer):
    """
    Combined serializer to list all commission types with improved error handling
    """
    id = serializers.IntegerField()
    name = serializers.CharField()
    description = serializers.CharField(allow_null=True)
    commission_type = serializers.CharField()
    commission_type_display = serializers.CharField(source='get_commission_type_display')
    percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    is_active = serializers.BooleanField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    details = serializers.SerializerMethodField()

    def get_details(self, obj):
        """Return specific details based on commission type with improved error handling"""
        try:
            if hasattr(obj, 'vendor_classification'):
                return {
                    'vendor_classification': obj.vendor_classification,
                    'vendor_classification_display': obj.get_vendor_classification_display()
                }
            elif hasattr(obj, 'start_date'):
                return {
                    'start_date': obj.start_date,
                    'end_date': obj.end_date
                }
            elif hasattr(obj, 'category'):
                return {
                    'category_id': obj.category_id,
                    'category_name': obj.category.name if obj.category else None,
                    'subcategory_id': obj.subcategory_id,
                    'subcategory_name': obj.subcategory.name if obj.subcategory else None
                }
            return {}
        except Exception as e:
            logger.error(f"Error in get_details: {str(e)}")
            return {'error': 'Could not retrieve commission details'}

