from django.db import models
from django.utils.text import slugify
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super(Category, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'


class SubCategory(models.Model):
    """
    SubCategory model for more detailed product organization
    """
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='subcategories'
    )
    name = models.CharField(max_length=100)
    slug = models.SlugField(blank=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='subcategories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super(SubCategory, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.category.name} - {self.name}"

    class Meta:
        verbose_name = 'SubCategory'
        verbose_name_plural = 'SubCategories'
        unique_together = ('category', 'name')

class DealStatus(models.TextChoices):
    """Status options for a deal"""
    PENDING = 'pending', _('Pending Review')
    APPROVED = 'approved', _('Approved')
    REJECTED = 'rejected', _('Rejected')
    EXPIRED = 'expired', _('Expired')
    CANCELED = 'canceled', _('Canceled')

class Deal(models.Model):
    """
    Model representing a deal between a client and vendor
    """
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='client_deals'
    )
    vendor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='vendor_deals'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='USD')
    category = models.ForeignKey(
        'superadmin.Category',
        on_delete=models.SET_NULL,
        null=True,
        related_name='deals'
    )
    subcategory = models.ForeignKey(
        'superadmin.SubCategory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deals'
    )
    status = models.CharField(
        max_length=20,
        choices=DealStatus.choices,
        default=DealStatus.PENDING
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_deals'
    )
    rejection_reason = models.TextField(blank=True, null=True)
    admin_notes = models.TextField(blank=True, null=True)
    terms = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expiry_date = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Deal'
        verbose_name_plural = 'Deals'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class Offer(models.Model):
    """
    Model representing vendor offers that can be reviewed by admins
    """
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()

    vendor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='offers'
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='USD')

    category = models.ForeignKey(
        'superadmin.Category',
        on_delete=models.SET_NULL,
        null=True,
        related_name='offers'
    )
    subcategory = models.ForeignKey(
        'superadmin.SubCategory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='offers'
    )

    is_active = models.BooleanField(default=True)
    is_approved = models.BooleanField(default=False)

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_offers'
    )
    rejection_reason = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expiry_date = models.DateTimeField(null=True, blank=True)

    has_violation = models.BooleanField(default=False)
    violation_notes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = 'Offer'
        verbose_name_plural = 'Offers'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.vendor.username}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

class CommissionType(models.TextChoices):
    """Type of commissions available in the system"""
    VENDOR_TYPE = 'vendor_type', _('Based on Vendor Classification')
    TIME_PERIOD = 'time_period', _('Based on Time Period')
    OFFER_TYPE = 'offer_type', _('Based on Offer Category')


class Commission(models.Model):
    """
    Base model for commission configurations
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    commission_type = models.CharField(
        max_length=20,
        choices=CommissionType.choices,
        default=CommissionType.VENDOR_TYPE
    )
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='%(class)s_created'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='%(class)s_updated'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.percentage}%"


class VendorTypeCommission(Commission):
    """
    Commission model based on vendor classification with default rates that can be adjusted
    """
    DEFAULT_RATES = {
        'bronze': 20.00,
        'silver': 15.00,
        'gold': 10.00,
        'platinum': 5.00,
        'special': None
    }

    vendor_classification = models.CharField(
        max_length=20,
        choices=[
            ('bronze', _('Bronze (Default: 20%)')),
            ('silver', _('Silver (Default: 15%)')),
            ('gold', _('Gold (Default: 10%)')),
            ('platinum', _('Platinum (Default: 5%)')),
            ('special', _('Special (Custom)'))
        ],
        unique=True
    )

    class Meta:
        verbose_name = 'Vendor Type Commission'
        verbose_name_plural = 'Vendor Type Commissions'
        constraints = [
            models.UniqueConstraint(
                fields=['vendor_classification', 'is_active'],
                condition=models.Q(is_active=True),
                name='unique_active_classification'
            )
        ]

    def clean(self):
        """Validate model before saving"""
        # Only validate that special classification has a percentage set
        if self.vendor_classification == 'special' and not self.percentage:
            raise ValidationError("Special commissions require a custom percentage")

    def save(self, *args, **kwargs):
        """Ensure only one active commission per classification"""
        # Ensure only one active commission per classification
        if self.is_active:
            VendorTypeCommission.objects.filter(
                vendor_classification=self.vendor_classification,
                is_active=True
            ).exclude(pk=self.pk).update(is_active=False)

        # If percentage not provided, set to default
        if self.percentage is None and self.vendor_classification != 'special':
            self.percentage = self.DEFAULT_RATES[self.vendor_classification]

        super().save(*args, **kwargs)

    @classmethod
    def get_default_for_classification(cls, classification):
        """Get or create default commission for a classification"""
        if classification == 'special':
            raise ValueError("Special commissions must be created explicitly")

        commission, created = cls.objects.get_or_create(
            vendor_classification=classification,
            defaults={
                'name': f"Default {classification} commission",
                'description': f"Standard {classification} vendor commission",
                'percentage': cls.DEFAULT_RATES[classification],
                'commission_type': CommissionType.VENDOR_TYPE,
                'is_active': True
            }
        )
        return commission


class TimePeriodCommission(Commission):
    """
    Commission model based on specific time periods (e.g., holidays, seasons)
    """
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    class Meta:
        verbose_name = 'Time Period Commission'
        verbose_name_plural = 'Time Period Commissions'

    def clean(self):
        """Validate that end_date is after start_date"""
        from django.core.exceptions import ValidationError
        if self.end_date <= self.start_date:
            raise ValidationError({'end_date': _('End date must be after start date')})


class OfferTypeCommission(Commission):
    """
    Commission model based on offer category
    """
    category = models.ForeignKey(
        'superadmin.Category',
        on_delete=models.CASCADE,
        related_name='category_commissions'
    )
    subcategory = models.ForeignKey(
        'superadmin.SubCategory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subcategory_commissions'
    )

    class Meta:
        verbose_name = 'Offer Type Commission'
        verbose_name_plural = 'Offer Type Commissions'
        unique_together = ['category', 'subcategory', 'is_active']