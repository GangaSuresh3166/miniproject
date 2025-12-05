from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, LoginOTP, Category, Supplier, Product,SystemLog,
    Purchase, PurchaseItem,SystemSetting,SystemConfig,
    SubCategory, Sales, SalesItem, Customer,AppearanceSettings)


# -----------------------------------------------------
# 1. CUSTOM USER ADMIN
# -----------------------------------------------------

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "phone", "is_staff", "is_active")
    list_filter = ("is_staff", "is_active")

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal Info", {"fields": ("first_name", "last_name", "email", "phone")}),
        ("Permissions", {
            "fields": (
                "is_active", "is_staff", "is_superuser",
                "groups", "user_permissions"
            )
        }),
        ("Important Dates", {"fields": ("last_login", "date_joined")}),
    )


# -----------------------------------------------------
# 2. SUPPLIER
# -----------------------------------------------------

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("supplier_name", "company_name", "phone", "email", "gst_number")
    search_fields = ("supplier_name", "company_name", "phone", "email")
    list_filter = ("city", "state")


# -----------------------------------------------------
# 3. CATEGORY / SUBCATEGORY
# -----------------------------------------------------

class SubCategoryInline(admin.TabularInline):
    model = SubCategory
    extra = 1
    fields = ("subcategory_name", "is_active")
    show_change_link = True


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "category_name", "is_active")
    search_fields = ("category_name",)
    list_filter = ("is_active",)
    ordering = ("category_name",)
    inlines = [SubCategoryInline]   # 🔥 Show all subcategories inside category admin


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "subcategory_name", "category", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("subcategory_name", "category__category_name")
    ordering = ("category__category_name", "subcategory_name")


# -----------------------------------------------------
# 4. PRODUCT
# -----------------------------------------------------

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "product_id", "name", "category", "brand",
        "cost_price", "selling_price", "quantity", "status"
    )

    list_filter = ("category", "brand", "status")
    search_fields = ("product_id", "name", "brand", "supplier_name")
    readonly_fields = ("product_id",)


# -----------------------------------------------------
# 5. PURCHASE + PURCHASE ITEM
# -----------------------------------------------------

class PurchaseItemInline(admin.TabularInline):
    model = PurchaseItem
    extra = 0
    fields = ("product", "quantity", "cost_price", "discount", "tax", "line_total")
    readonly_fields = ("line_total",)


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = (
        "id", "purchase_no", "supplier",
        "date", "subtotal", "grand_total", "balance"
    )
    list_filter = ("supplier", "date")
    search_fields = ("purchase_no", "supplier__supplier_name")
    inlines = [PurchaseItemInline]

# -----------------------------------------------------
# 7. LOGIN OTP
# -----------------------------------------------------

@admin.register(LoginOTP)
class LoginOTPAdmin(admin.ModelAdmin):
    list_display = ("user", "code", "created_at", "expires_at", "used", "attempts")
    list_filter = ("used",)
    search_fields = ("user__username", "code")


# -----------------------------------------------------
# 8. SYSTEM SETTINGS
# -----------------------------------------------------

@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ("site_name", "contact_email", "contact_phone", "last_updated")


@admin.register(SystemConfig)
class SystemConfigAdmin(admin.ModelAdmin):
    list_display = ("system_name", "currency", "default_tax")


@admin.register(SystemLog)
class SystemLogAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "user", "action")
    search_fields = ("action", "user__username")
    list_filter = ("timestamp",)


@admin.register(AppearanceSettings)
class AppearanceSettingsAdmin(admin.ModelAdmin):
    list_display = ("theme",)


# -----------------------------------------------------
# 9. CUSTOM ADMIN SITE ADD-ON (Admin Logs)
# -----------------------------------------------------

class CustomAdminSite(admin.AdminSite):
    """Adds custom link to admin logs page."""
    site_header = "Stock App Admin"
    site_title = "Stock App"
    index_title = "Dashboard"

    def each_context(self, request):
        context = super().each_context(request)
        context["custom_logs_url"] = reverse("admin_logs")
        return context


admin_site = CustomAdminSite()



