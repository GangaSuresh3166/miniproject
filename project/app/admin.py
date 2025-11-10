from django.contrib import admin
from .models import (
    UserProfile, LoginOTP, Category, Supplier, Product,
    Transaction, Report, Purchase, Sale,
    StockReport, SystemSetting, SystemConfig, SystemLog,
    AppearanceSettings
)





# ✅ LOGIN OTP
@admin.register(LoginOTP)
class LoginOTPAdmin(admin.ModelAdmin):
    list_display = ("user", "code", "created_at", "expires_at", "used", "attempts")
    list_filter = ("used",)
    search_fields = ("user__username", "code")


# ✅ CATEGORY
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "description")
    search_fields = ("name",)


# ✅ SUPPLIER
@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "email", "phone", "address")
    search_fields = ("name", "email", "phone")


# ✅ PRODUCT
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "category", "supplier", "price", "stock")
    search_fields = ("name",)
    list_filter = ("category", "supplier")
    autocomplete_fields = ("category", "supplier")


# ✅ TRANSACTIONS
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "quantity", "transaction_type", "date")
    list_filter = ("transaction_type", "date")
    search_fields = ("product__name",)


# ✅ REPORTS
@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at")
    search_fields = ("name",)


# ✅ PURCHASES
@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ("id", "supplier", "product", "quantity", "purchase_price", "total_cost", "date")
    search_fields = ("supplier__name", "product__name")
    list_filter = ("date",)
    autocomplete_fields = ("supplier", "product")


# ✅ SALES
@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "quantity", "sale_price", "total_amount", "customer_name", "date")
    search_fields = ("product__name", "customer_name")
    list_filter = ("date",)
    autocomplete_fields = ("product",)


# ✅ STOCK REPORTS
@admin.register(StockReport)
class StockReportAdmin(admin.ModelAdmin):
    list_display = ("id", "generated_on", "total_products", "total_stock_value", "generated_by")
    list_filter = ("generated_on",)


# ✅ SYSTEM SETTINGS
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
