from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from superadmin.models import VendorTypeCommission

class User(AbstractUser):

    class UserType(models.TextChoices):
        SUPERADMIN = 'superadmin', _('Super Admin')
        CLIENT = 'client', _('Client')
        VENDOR = 'vendor', _('Vendor')
        FINANCIAL = 'financial', _('Financial Manager')
        TECHNICAL = 'technical', _('Technical Support')

    user_type = models.CharField(
        max_length=20,
        choices=UserType.choices,
        default=UserType.CLIENT,
    )
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')

    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"

    @property
    def is_superadmin(self):
        return self.user_type == self.UserType.SUPERADMIN

    @property
    def is_client(self):
        return self.user_type == self.UserType.CLIENT

    @property
    def is_vendor(self):
        return self.user_type == self.UserType.VENDOR

    @property
    def is_financial(self):
        return self.user_type == self.UserType.FINANCIAL

    @property
    def is_technical(self):
        return self.user_type == self.UserType.TECHNICAL


#Additional user information based on user type
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    address = models.TextField(blank=True, null=True)
    company_name = models.CharField(max_length=100, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Profile for {self.user.username}"


class VendorClassification(models.TextChoices):
    BRONZE = 'bronze', 'Bronze (20%)'
    SILVER = 'silver', 'Silver (15%)'
    GOLD = 'gold', 'Gold (10%)'
    PLATINUM = 'platinum', 'Platinum (5%)'


    @property
    def default_rate(self):
        """Returns the static commission rate for each classification"""
        rates = {
            'bronze': 20.00,
            'silver': 15.00,
            'gold': 10.00,
            'platinum': 5.00,
            'special': None
        }
        return rates.get(self.value)

class VendorProfile(models.Model):
    """
    Extended profile for vendors with additional details
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='vendor_profile'
    )

    business_name = models.CharField(max_length=200, blank=True, null=True)
    business_registration_number = models.CharField(max_length=100, unique=True)
    business_type = models.CharField(max_length=100, blank=True, null=True)

    classification = models.CharField(
        max_length=20,
        choices=VendorClassification.choices,
        default=VendorClassification.BRONZE
    )

    phone_number = models.CharField(max_length=20, blank=True, null=True)
    alternative_phone = models.CharField(max_length=20, blank=True, null=True)
    business_email = models.EmailField(blank=True, null=True)

    headquarters_address = models.TextField(blank=True, null=True)

    working_hours = models.JSONField(
        blank=True,
        null=True,
        help_text='Store working hours in JSON format'
    )

    trade_license = models.FileField(
        upload_to='vendor_documents/trade_licenses/',
        blank=True,
        null=True
    )
    tax_certificate = models.FileField(
        upload_to='vendor_documents/tax_certificates/',
        blank=True,
        null=True
    )
    business_registration_document = models.FileField(
        upload_to='vendor_documents/registration_docs/',
        blank=True,
        null=True
    )

    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='verified_vendors',
        blank=True,
        null=True
    )
    verification_notes = models.TextField(blank=True, null=True)

    branches = models.JSONField(
        blank=True,
        null=True,
        help_text='Store branch information in JSON format'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.business_name or self.user.username} - {self.classification}"

    def get_commission_rate(self):
        """Get the applicable commission rate for this vendor"""
        if self.classification == 'special' and hasattr(self, 'custom_commission'):
            return self.custom_commission.percentage

        try:
            commission = VendorTypeCommission.objects.get(
                vendor_classification=self.classification,
                is_active=True
            )
            return commission.percentage
        except VendorTypeCommission.DoesNotExist:
            return VendorTypeCommission.CLASSIFICATION_RATES.get(self.classification)

    def save(self, *args, **kwargs):
        """Ensure default commission exists for vendor's classification"""
        super().save(*args, **kwargs)
        if self.classification != 'special':
            VendorTypeCommission.get_default_for_classification(self.classification)

    class Meta:
        verbose_name = 'Vendor Profile'
        verbose_name_plural = 'Vendor Profiles'
        unique_together = ['user', 'business_registration_number']