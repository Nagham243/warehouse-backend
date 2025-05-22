from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import UserProfile,VendorProfile, VendorClassification

User = get_user_model()

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['id', 'address', 'company_name', 'bio']



class UserListSerializer(serializers.ModelSerializer):
    user_type_display = serializers.CharField(source='get_user_type_display', read_only=True)
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'user_type', 'user_type_display', 'is_active', 'created_at'
        ]


class UserDetailSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    user_type_display = serializers.CharField(source='get_user_type_display', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'user_type', 'user_type_display', 'phone_number',
            'profile_image', 'is_active', 'is_staff',
            'created_at', 'updated_at', 'profile'
        ]
        read_only_fields = ['created_at', 'updated_at']


class UserCreateSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    profile = UserProfileSerializer(required=False)

    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'user_type', 'phone_number',
            'profile_image', 'profile'
        ]

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        profile_data = validated_data.pop('profile', None)

        user = User.objects.create_user(**validated_data)

        if profile_data:
            UserProfile.objects.create(user=user, **profile_data)
        else:
            UserProfile.objects.create(user=user)

        return user

class UserUpdateSerializer(serializers.ModelSerializer):

    profile = UserProfileSerializer(required=False)

    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name', 'user_type',
            'phone_number', 'profile_image', 'is_active', 'profile'
        ]

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if profile_data:
            profile = instance.profile
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()

        return instance


class PasswordChangeSerializer(serializers.Serializer):

    old_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    new_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    new_password_confirm = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    def validate(self, data):
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError({"new_password": "Password fields didn't match."})
        return data

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is not correct")
        return value

class UserStatusUpdateSerializer(serializers.Serializer):
    is_active = serializers.BooleanField(required=True)



class VendorRegistrationSerializer(serializers.Serializer):
    """
    Serializer for vendor registration process with file upload support
    """
    # User fields
    username = serializers.CharField(required=True, max_length=150)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        min_length=8
    )
    confirm_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )

    # Vendor profile fields
    business_name = serializers.CharField(required=True, max_length=200)
    business_registration_number = serializers.CharField(
        required=True,
        max_length=100
    )
    phone_number = serializers.CharField(required=True, max_length=20)
    business_type = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=100
    )

    # JSON fields
    working_hours = serializers.JSONField(
        required=False,
        allow_null=True,
        help_text="Working hours in JSON format"
    )
    branches = serializers.JSONField(
        required=False,
        allow_null=True,
        help_text="Branch information in JSON format"
    )

    # File fields
    trade_license = serializers.FileField(
        required=False,
        allow_null=True,
        max_length=255,
        help_text="Upload trade license document"
    )
    tax_certificate = serializers.FileField(
        required=False,
        allow_null=True,
        max_length=255,
        help_text="Upload tax certificate document"
    )
    business_registration_document = serializers.FileField(
        required=False,
        allow_null=True,
        max_length=255,
        help_text="Upload business registration document"
    )

    def validate(self, attrs):
        """
        Validate password confirmation and unique constraints
        """
        errors = {}

        # Password confirmation
        if attrs['password'] != attrs['confirm_password']:
            errors['confirm_password'] = "Passwords do not match"

        # Unique username check
        if User.objects.filter(username=attrs['username']).exists():
            errors['username'] = "A user with this username already exists"

        # Unique email check
        if User.objects.filter(email=attrs['email']).exists():
            errors['email'] = "A user with this email already exists"

        # Unique business registration number check
        if VendorProfile.objects.filter(
                business_registration_number=attrs['business_registration_number']
        ).exists():
            errors['business_registration_number'] = "A vendor with this registration number already exists"

        if errors:
            raise serializers.ValidationError(errors)

        return attrs

    def create(self, validated_data):
        """
        Create user and vendor profile with uploaded documents
        """
        # Extract user data
        user_data = {
            'username': validated_data.pop('username'),
            'email': validated_data.pop('email'),
            'password': validated_data.pop('password'),
            'user_type': User.UserType.VENDOR,
            'phone_number': validated_data.pop('phone_number')
        }

        # Remove confirm_password as it's no longer needed
        validated_data.pop('confirm_password')

        # Create user
        user = User.objects.create_user(**user_data)

        # Create vendor profile
        vendor_profile = VendorProfile.objects.create(
            user=user,
            **validated_data
        )

        return user

class VendorProfileSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for vendor profile
    """
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    user_type = serializers.CharField(source='user.user_type', read_only=True)
    commission_rate = serializers.SerializerMethodField()
    trade_license = serializers.SerializerMethodField()
    tax_certificate = serializers.SerializerMethodField()
    business_registration_document = serializers.SerializerMethodField()

    def get_commission_rate(self, obj):
        return obj.get_commission_rate()

    def get_trade_license(self, obj):
        if obj.trade_license:
            return self.context['request'].build_absolute_uri(obj.trade_license.url)
        return None

    def get_tax_certificate(self, obj):
        if obj.tax_certificate:
            return self.context['request'].build_absolute_uri(obj.tax_certificate.url)
        return None

    def get_business_registration_document(self, obj):
        if obj.business_registration_document:
            return self.context['request'].build_absolute_uri(obj.business_registration_document.url)
        return None

    class Meta:
        model = VendorProfile
        fields = [
            'id', 'user', 'username', 'email', 'user_type',
            'business_name', 'business_registration_number',
            'business_type', 'classification',
            'phone_number', 'alternative_phone', 'business_email',
            'headquarters_address', 'working_hours', 'branches',
            'is_verified', 'verification_notes',
            'created_at', 'updated_at', 'commission_rate',
            'trade_license', 'tax_certificate', 'business_registration_document'
        ]
        read_only_fields = [
            'id', 'user', 'username', 'email', 'user_type',
            'created_at', 'updated_at', 'is_verified'
        ]



class VendorVerificationSerializer(serializers.ModelSerializer):
    """
    Serializer for superadmin to verify and manage vendor profiles
    """
    class Meta:
        model = VendorProfile
        fields = [
            'classification',
            'is_verified',
            'verification_notes'
        ]

    def update(self, instance, validated_data):
        validated_data['verified_by'] = self.context['request'].user
        return super().update(instance, validated_data)

class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for general user registration
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    confirm_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'password',
            'confirm_password',
            'user_type'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'user_type': {'required': False}
        }

    def validate(self, attrs):
        """
        Validate password confirmation and unique constraints
        """
        if attrs.get('password') != attrs.get('confirm_password'):
            raise serializers.ValidationError({"confirm_password": "Passwords do not match"})

        username = attrs.get('username')
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError({"username": "A user with this username already exists"})

        email = attrs.get('email')
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError({"email": "A user with this email already exists"})

        return attrs

    def create(self, validated_data):
        """
        Create user removing confirm_password before saving
        """
        validated_data.pop('confirm_password')
        user = User.objects.create_user(**validated_data)
        return user

class SuperAdminSerializer(serializers.ModelSerializer):
    """
    Serializer specific for superadmin users with additional system information
    """
    profile = serializers.SerializerMethodField()
    system_stats = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone_number', 'profile_image', 'created_at', 'updated_at',
            'profile', 'system_stats'
        ]
        read_only_fields = ['created_at', 'updated_at', 'system_stats']

    def get_profile(self, obj):
        """
        Get the superadmin's profile with additional fields
        """
        try:
            profile = obj.profile
            return {
                'id': profile.id,
                'address': profile.address,
                'company_name': profile.company_name,
                'bio': profile.bio,
                'last_login': obj.last_login,
                'is_superuser': obj.is_superuser,
                'is_staff': obj.is_staff
            }
        except UserProfile.DoesNotExist:
            return None

class SuperAdminProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating superadmin profile information
    """
    profile = serializers.JSONField(required=False)

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email',
            'phone_number', 'profile_image', 'profile'
        ]

    def update(self, instance, validated_data):
        """
        Update the superadmin user and their profile
        """
        profile_data = validated_data.pop('profile', None)

        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update profile fields if provided
        if profile_data and isinstance(profile_data, dict):
            profile = instance.profile
            allowed_fields = ['address', 'company_name', 'bio']

            for field in allowed_fields:
                if field in profile_data:
                    setattr(profile, field, profile_data[field])
            profile.save()

        return instance
