from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.contrib.auth.models import User
from django.conf import settings
import uuid


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ("staff", "Staff"),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=20, blank=True, null=True)
    company = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.user.username



class LoginOTP(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    attempts = models.PositiveSmallIntegerField(default=0)

    def is_valid(self):
        return (
            not self.used and 
            timezone.now() <= self.expires_at and 
            self.attempts < 5
        )

    def __str__(self):
        return f"{self.user} — {self.code}"



# -----------------------------
# Category model
# -----------------------------
class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

# -----------------------------
# Supplier model
# -----------------------------
class Supplier(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return self.name


# -----------------------------
# Product model
# -----------------------------
class Product(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)  # ✅ Add this
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name



# -----------------------------
# Transaction model
# -----------------------------
class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('sale', 'Sale'),
        ('purchase', 'Purchase'),
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type.title()} - {self.product.name}"


# -----------------------------
# Report model
# -----------------------------
class Report(models.Model):
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name   # ✅ fixed — use existing field


# ----------------------------21


class Purchase(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='purchases')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='purchases')
    quantity = models.PositiveIntegerField()
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    date = models.DateField(default=timezone.now)

    def save(self, *args, **kwargs):
        self.total_cost = self.quantity * self.purchase_price
        super().save(*args, **kwargs)
        # Update stock
        self.product.quantity += self.quantity
        self.product.save()

    def __str__(self):
        return f"Purchase of {self.product.name} ({self.quantity})"


class Sale(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='sales')
    quantity = models.PositiveIntegerField()
    sale_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    date = models.DateField(default=timezone.now)
    customer_name = models.CharField(max_length=150, blank=True)

    def save(self, *args, **kwargs):
        self.total_amount = self.quantity * self.sale_price
        super().save(*args, **kwargs)
        # Update stock
        self.product.quantity -= self.quantity
        self.product.save()

    def __str__(self):
        return f"Sale of {self.product.name} ({self.quantity})"


# -------------------------------------------------------
# 7️⃣ Stock Report Model
# -------------------------------------------------------
class StockReport(models.Model):
    generated_on = models.DateTimeField(auto_now_add=True)
    total_products = models.PositiveIntegerField()
    total_stock_value = models.DecimalField(max_digits=12, decimal_places=2)
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # ✅ instead of User
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"Report - {self.generated_on.strftime('%Y-%m-%d %H:%M')}"



# -------------------------------------------------------
# 8️⃣ System Settings (for admin configuration)
# -------------------------------------------------------
class SystemSetting(models.Model):
    site_name = models.CharField(max_length=150, default="Stock Inventory System")
    logo = models.ImageField(upload_to='settings/', blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "System Settings"



class SystemConfig(models.Model):
    system_name = models.CharField(max_length=200, default="Inventory Management System")
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
    theme = models.CharField(max_length=20, default="light")  # light / dark / blue

    def __str__(self):
        return self.theme




class PasswordResetOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_otps')
    otp = models.CharField(max_length=6)                 # numeric string like '123456'
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    token = models.UUIDField(default=uuid.uuid4, editable=False)  # optional extra token

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"OTP for {self.user.email} (used={self.used})"
