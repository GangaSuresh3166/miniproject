from app import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

app_name = "app"
urlpatterns = [

    # -----------------------
    # AUTH & OTP
    # -----------------------
    path("admin/", admin.site.urls),
    path("index/", views.index, name="index"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
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
    path("suppliers/add/", views.supplier_add, name="supplier_add"),
    path("suppliers/edit/<int:supplier_id>/", views.supplier_edit, name="supplier_edit"),
    path("suppliers/delete/<int:supplier_id>/", views.supplier_delete, name="supplier_delete"),


    # -----------------------
    # PRODUCTS
    # -----------------------

    path("products/", views.product_list, name="product_list"),
    path("products/add/", views.product_add, name="product_add"),
    path("products/edit/<int:pk>/", views.product_edit, name="product_edit"),
    path("products/delete/<int:pk>/", views.product_delete, name="product_delete"),
    path("get-subcategories/", views.get_subcategories, name="get_subcategories"),

   
    # -----------------------
    # CATEGORIES SYSTEM
    # -----------------------
    
    path("categories/", views.category_list, name="category_list"),
    path("categories/add/", views.category_add, name="category_add"),
    path("categories/edit/<int:pk>/", views.category_edit, name="category_edit"),
    path("categories/delete/<int:pk>/", views.category_delete, name="category_delete"),

    # -----------------------
    # PURCHASE SYSTEM
    # -----------------------


    path("purchases/", views.purchase_list, name="purchase_list"),
    path('purchase/add/', views.purchase_add, name='purchase_add'),
    path('api/supplier/<int:pk>/', views.supplier_detail_json, name='supplier_detail_json'),
    path('api/product/<int:pk>/', views.product_detail_json, name='product_detail_json'),
    path("purchases/<int:pk>/edit/", views.purchase_edit, name="purchase_edit"),
    path("purchases/<int:pk>/delete/", views.purchase_delete, name="purchase_delete"),


    # -----------------------
    # Sales SYSTEM
    # -----------------------

    path("sales/", views.sales_list, name="sales_list"),
    path("sales/add/", views.sales_add, name="sales_add"),
    path("sales/<int:pk>/edit/", views.sales_edit, name="sales_edit"),
    path("sales/<int:pk>/delete/", views.sales_delete, name="sales_delete"),
    


    # -----------------------
    # SUBCATEGORY SYSTEM
    # -----------------------

    path("subcategories/", views.subcategory_list, name="subcategory_list"),
    path("subcategories/add/", views.subcategory_add, name="subcategory_add"),
    path("subcategories/edit/<int:pk>/", views.subcategory_edit, name="subcategory_edit"),
    path("subcategories/delete/<int:pk>/", views.subcategory_delete, name="subcategory_delete"),



    path('user_home/', views.user_home, name='user_home'),
    path("user_sales_list/", views.user_sales_list, name="user_sales_list"),
    path("user_sales_add/", views.user_sales_add, name="user_sales_add"),
    path("user_sales_edit/<int:pk>/",views. user_sales_edit, name="user_sales_edit"),
    path("user_sales_delete/<int:pk>/", views.user_sales_delete, name="user_sales_delete"),
    path("profile/", views.user_profile, name="user_profile"),
    path("edit_profile/", views.edit_profile, name="edit_profile"),

    path("request_otp/", views.request_otp_view, name="request_otp"),
    path("verify_otp/", views.verify_otp_view, name="verify_otp"),
    path("reset_password/", views.reset_password_view, name="reset_password"),
    path("analytics/",views.analytics_view, name="analytics"),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

