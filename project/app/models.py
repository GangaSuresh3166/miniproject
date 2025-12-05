from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.conf import settings


# =====================================================
# 1. CUSTOM USER
# =====================================================

class User(AbstractUser):
    phone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.username


# =====================================================
# 2. CUSTOMER
# =====================================================

class Customer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return self.name


# =====================================================
# 3. SUPPLIER
# =====================================================

class Supplier(models.Model):
    supplier_name = models.CharField(max_length=150)
    company_name = models.CharField(max_length=200, blank=True, null=True)

    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20)
    alt_phone = models.CharField(max_length=20, blank=True, null=True)

    gst_number = models.CharField(max_length=50, blank=True, null=True)
    pan_number = models.CharField(max_length=50, blank=True, null=True)

    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, default="India")
    postal_code = models.CharField(max_length=15, blank=True, null=True)

    bank_name = models.CharField(max_length=150, blank=True, null=True)
    account_number = models.CharField(max_length=50, blank=True, null=True)
    ifsc_code = models.CharField(max_length=20, blank=True, null=True)
    branch = models.CharField(max_length=100, blank=True, null=True)

    website = models.CharField(max_length=150, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["supplier_name"]

    def __str__(self):
        return self.supplier_name


# =====================================================
# 4. CATEGORY & SUBCATEGORY
# =====================================================

class Category(models.Model):
    category_name = models.CharField(max_length=150, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.category_name


class SubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="subcategories")
    subcategory_name = models.CharField(max_length=150, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.subcategory_name


# =====================================================
# 5. PRODUCT (FULL MODEL)
# =====================================================

class Product(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('out_of_stock', 'Out of Stock'),
        ('discontinued', 'Discontinued'),
    ]

    product_id = models.CharField(max_length=50)
    name = models.CharField(max_length=200)

    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    subcategory = models.ForeignKey(SubCategory, on_delete=models.SET_NULL, null=True)

    brand = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    cost_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    discount = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    tax = models.DecimalField(max_digits=5, decimal_places=2, null=True)

    quantity = models.IntegerField()
    reorder_level = models.IntegerField()

    supplier_name = models.CharField(max_length=200, null=True)
    supplier_contact = models.CharField(max_length=20, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


# =====================================================
# 6. SALES & SALES ITEMS
# =====================================================


class Sales(models.Model):
    PAYMENT_STATUS_CHOICES = (
        ("PAID", "Paid"),
        ("PENDING", "Pending"),
        ("CREDIT", "Credit"),
    )

    invoice_no = models.CharField(max_length=20, unique=True)
    customer_name = models.CharField(max_length=200, null=True)
    date = models.DateField(blank=True, null=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    payment_status = models.CharField(
        max_length=10, choices=PAYMENT_STATUS_CHOICES, default="PENDING"
    )

    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Invoice #{self.invoice_no} - {self.customer_name}"

class SalesItem(models.Model):
    sale = models.ForeignKey(Sales, related_name="items", on_delete=models.CASCADE,null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE,null=True)
    qty = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2,null=True)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)



# =====================================================
# 7. PURCHASE & PURCHASE ITEMS
# =====================================================

class Purchase(models.Model):
    PAYMENT_TYPES = [
        ("cash", "Cash"),
        ("card", "Card"),
        ("online", "Online Transfer"),
        ("credit", "Credit"),
    ]

    PAYMENT_STATUS = [
        ("paid", "Paid"),
        ("partial", "Partial"),
        ("unpaid", "Unpaid"),
    ]

    purchase_no = models.CharField(max_length=50, unique=True)
    date = models.DateField(default=timezone.now)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Purchase #{self.purchase_no}"


class PurchaseItem(models.Model):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    qty = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    discount = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    tax = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    line_total = models.DecimalField(max_digits=10, decimal_places=2, null=True)

    def __str__(self):
        return f"{self.product.name} x {self.qty}"


# =====================================================
# 9. OTP & SYSTEM SETTINGS
# =====================================================

class LoginOTP(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    attempts = models.PositiveSmallIntegerField(default=0)

    def is_valid(self):
        return (
            not self.used
            and timezone.now() <= self.expires_at
            and self.attempts < 5
        )

    def __str__(self):
        return f"{self.user} — {self.code}"


class SystemSetting(models.Model):
    site_name = models.CharField(max_length=150, default="Stock App System")
    logo = models.ImageField(upload_to="settings/", blank=True, null=True)

    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=20, blank=True, null=True)

    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "System Settings"


class SystemConfig(models.Model):
    system_name = models.CharField(max_length=200, default="App Management System")
    currency = models.CharField(max_length=20, default="INR (₹)")
    default_tax = models.FloatField(default=0)

    def __str__(self):
        return self.system_name


class SystemLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=255)
    details = models.TextField(blank=True)

    def __str__(self):
        return f"{self.timestamp} - {self.action}"


class AppearanceSettings(models.Model):
    theme = models.CharField(max_length=20, default="light")

    def __str__(self):
        return self.theme


class PasswordResetOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"{self.user.email} - {self.otp}"
