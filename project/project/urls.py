from django.urls import path
from app import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [

    # -----------------------
    # AUTH & OTP
    # -----------------------

    path("index/", views.index, name="index"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    path("registration/", views.registration, name="registration"),

    path("otp-request/", views.otp_request, name="otp_request"),
    path("otp-verify/", views.otp_verify, name="otp_verify"),

    # -----------------------
    # ADMIN HOME / DASHBOARD
    # -----------------------
    path("admin_home/", views.admin_home, name="admin_home"),

    # -----------------------
    # USER MANAGEMENT
    # -----------------------
    path("users/", views.users_list, name="users_list"),
    path("users_add/", views.add_user, name="add_user"),
    path("users_edit/<int:user_id>/", views.edit_user, name="edit_user"),
    path("users_delete/<int:user_id>/", views.delete_user, name="delete_user"),

    # -----------------------
    # SUPPLIERS
    # -----------------------
    path("suppliers/", views.supplier_list, name="supplier_list"),
    path("suppliers_add/", views.add_supplier, name="add_supplier"),
    path("suppliers_edit/<int:supplier_id>/", views.edit_supplier, name="edit_supplier"),
    path("suppliers_delete/<int:supplier_id>/", views.delete_supplier, name="delete_supplier"),

    # -----------------------
    # PRODUCTS
    # -----------------------

    path("products_list/", views.product_list, name="product_list"),
    path("products_add/", views.add_product, name="add_product"),
    path("products_edit/<int:pk>/", views.edit_product, name="edit_product"),
    path("products_delete/<int:pk>/", views.delete_product, name="delete_product"),

    # -----------------------
    # CATEGORIES
    
    path("categories_add/", views.add_category, name="add_edit_category"),
    path("categories_edit/<int:pk>/", views.edit_category, name="add_edit_category"),
    path("categories_delete/<int:pk>/", views.delete_category, name="delete_category"),
    path("categories/", views.category_list, name="category_list"),


    # -----------------------
    # PURCHASE SYSTEM
    # -----------------------
    path("purchases/", views.purchase_list, name="purchase_list"),
    path("purchases_add/", views.add_purchase, name="add_purchase"),
    path("purchases_edit/<int:purchase_id>/", views.edit_purchase, name="edit_purchase"),
    path("purchases_delete/<int:purchase_id>/", views.delete_purchase, name="delete_purchase"),

    # -----------------------
    # SALES SYSTEM
    # -----------------------
    path("sales/", views.sales_list, name="sales_list"),
    path("sales_add", views.add_sales, name="add_sales"),
    path("sales_edit/<int:sales_id>/", views.edit_sales, name="edit_sales"),
    path("sales_delete/<int:sales_id>/", views.delete_sales, name="delete_sales"),

    # -----------------------
    # TRANSACTIONS SUMMARY
    # -----------------------
    path("transactions/", views.transactions, name="transactions"),

    # -----------------------
    # REPORTS
    # -----------------------
    path("reports/", views.report_dashboard, name="report_dashboard"),
    path("stock_ummary/", views.stock_summary, name="stock_summary"),
    path("stock_eport/", views.stock_report, name="stock_report"),
    path("stock_eport/export-csv/", views.stock_report_export_csv, name="stock_report_export_csv"),

    # -----------------------
    # SYSTEM SETTINGS
    # -----------------------
    path("settings/", views.settings_view, name="settings"),
    path("system_config/", views.system_config, name="system_config"),
    path("backup_restore/", views.backup_restore, name="backup_restore"),
    path("admin/logs/", views.admin_logs, name="admin_logs"),
    path("security_settings/", views.security_settings, name="security_settings"),
    path("appearance_settings/", views.appearance_settings, name="appearance_settings"),


    path('user_home/', views.user_home, name='user_home'),

    path('user_products/', views.user_product_list, name='user_product_list'),
    path('user_products/<int:id>/', views.user_product_detail, name='user_product_detail'),
    path('user_purchases/', views.user_purchase_list, name='user_purchase_list'),
    path('user_sales/', views.user_sales_list, name='user_sales_list'),
    path('user_profile/', views.user_profile, name='user_profile'),
    path('user_settings/', views.user_settings, name='user_settings'),
    path('user_reports/', views.user_reports, name='user_reports'),


    path('password_request-otp/', views.request_otp_view, name='request-otp'),
    path('password_verify-otp/', views.verify_otp_view, name='verify-otp'),
    path('password_reset/', views.reset_password_view, name='reset-password'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

