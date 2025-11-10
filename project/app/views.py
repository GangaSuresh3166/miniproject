from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.utils import timezone
from django.db.models import Count
from django.http import HttpResponse
from django.conf import settings
from django.urls import reverse
from django.contrib.auth.models import User
from .models import (
    Supplier, Product, Category, Transaction, UserProfile,
    LoginOTP, SystemConfig, SystemLog, AppearanceSettings,
    Purchase, Sale, PasswordResetOTP
)
from .forms import (
    RequestOTPForm, VerifyOTPForm, ResetPasswordForm,
    UserForm, ProductForm
)
from .utils import create_otp_for_user, send_otp_email
import random, csv, os, json
from datetime import timedelta


User = get_user_model()

# ---------------------------
# LOGIN / LOGOUT / REGISTER
# ---------------------------

def index(request):
    return render(request, "index.html")

def login_view(request):
    if request.method == "POST":
        fullname = request.POST.get("fullname")
        password = request.POST.get("password")

        # ✅ authenticate using fullname as username
        user = authenticate(request, username=fullname, password=password)

        if user is None:
            messages.error(request, "Invalid name or password")
            return redirect("login")

        login(request, user)

        # ✅ ADMIN → admin home
        if user.is_superuser or user.is_staff:
            return redirect('/admin_home/')

        # ✅ USER → user home
        return redirect('/user_home/')

    return render(request, "login.html")

def logout_view(request):
    logout(request)
    return redirect("login")


# app/views.py

def registration(request):
    if request.method == "POST":

        fullname = request.POST.get("fullname")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        role = request.POST.get("role")
        company = request.POST.get("company")
        password = request.POST.get("password")
        confirm = request.POST.get("confirm")

        # 1. Password match check
        if password != confirm:
            messages.error(request, "Passwords do not match.")
            return redirect("registration")

        # 2. Prevent duplicate accounts
        if User.objects.filter(username=fullname).exists():
            messages.error(request, "An account with this email already exists.")
            return redirect("registration")

        # 3. Block admin creation
        if role not in ["staff"]:
            messages.error(request, "Invalid role selected.")
            return redirect("registration")

        # 4. Create User
        user = User.objects.create_user(
    username=fullname,   # ✅ login with fullname
    email=email,
    password=password,
    first_name=fullname
)



        # Make sure it's never admin
        user.is_staff = False
        user.is_superuser = False
        user.save()

        # 5. Fill UserProfile
        profile = user.userprofile
        profile.role = role
        profile.phone = phone
        profile.company = company
        profile.save()

        messages.success(request, "Account created successfully! Please log in.")
        return redirect("login")

    return render(request, "registration.html")



# ---------------------------
# OTP AUTH
# ---------------------------

def otp_request(request):
    if request.method == "POST":
        identifier = request.POST.get("identifier")
        user = None

        # Identify user
        if "@" in identifier:
            user = User.objects.filter(email__iexact=identifier).first()
        else:
            user = User.objects.filter(username__iexact=identifier).first()

        if not user:
            messages.error(request, "User not found")
            return render(request, "otp_request.html")

        code = f"{random.randint(0, 999999):06d}"
        LoginOTP.objects.create(
            user=user,
            code=code,
            expires_at=timezone.now() + timedelta(minutes=10)
        )

        request.session["otp_uid"] = user.id
        return redirect("otp_verify")

    return render(request, "otp_request.html")


def otp_verify(request):
    uid = request.session.get("otp_uid")
    if not uid:
        return redirect("otp_request")

    user = User.objects.get(id=uid)

    if request.method == "POST":
        code = request.POST.get("code")

        otp = LoginOTP.objects.filter(user=user, used=False).latest("created_at")

        if not otp.is_valid():
            messages.error(request, "OTP expired or invalid")
            return redirect("otp_request")

        if otp.code == code:
            otp.used = True
            otp.save()
            login(request, user)
            return redirect("admin_home")

        messages.error(request, "Invalid code")

    return render(request, "otp_verify.html")

# ---------------------------
# ADMIN HOME / DASHBOARD
# ---------------------------

@login_required
def admin_home(request):
    total_users = User.objects.count()
    total_suppliers = Supplier.objects.count()
    total_products = Product.objects.count()
    total_transactions = Transaction.objects.count()

    total_sales = Sale.objects.count()
    total_purchases = Purchase.objects.count()

    context = {
        "total_users": total_users,
        "total_suppliers": total_suppliers,
        "total_products": total_products,
        "total_transactions": total_transactions,
        "total_sales": total_sales,
        "total_purchases": total_purchases,
    }

    return render(request, "admin_home.html", context)

# ---------------------------
# USER MANAGEMENT
# ---------------------------

@login_required
def users_list(request):
    users = User.objects.all().order_by("-date_joined")
    return render(request, "users_list.html", {"users": users})


@login_required
def add_user(request):
    if request.method == "POST":
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            if form.cleaned_data["password"]:
                user.set_password(form.cleaned_data["password"])
            user.save()
            messages.success(request, "User created successfully!")
            return redirect("users_list")
    else:
        form = UserForm()

    return render(request, "add_edit_user.html", {"form": form})


@login_required
def edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save(commit=False)
            if form.cleaned_data["password"]:
                user.set_password(form.cleaned_data["password"])
            user.save()
            messages.success(request, "User updated successfully!")
            return redirect("users_list")

    else:
        form = UserForm(instance=user)

    return render(request, "add_edit_user.html", {"form": form})


@login_required
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.delete()
    messages.success(request, "User deleted successfully!")
    return redirect("users_list")

# ---------------------------
# SUPPLIER MANAGEMENT
# ---------------------------

@login_required
def supplier_list(request):
    suppliers = Supplier.objects.all()
    return render(request, "supplier_list.html", {"suppliers": suppliers})


@login_required
def add_supplier(request):
    if request.method == "POST":
        Supplier.objects.create(
            name=request.POST["name"],
            email=request.POST.get("email"),
            phone=request.POST.get("phone"),
            address=request.POST.get("address"),
            is_active=(request.POST.get("is_active") == "True")
        )
        return redirect("supplier_list")

    return render(request, "add_edit_supplier.html")


@login_required
def edit_supplier(request, supplier_id):
    supplier = get_object_or_404(Supplier, id=supplier_id)

    if request.method == "POST":
        supplier.name = request.POST["name"]
        supplier.email = request.POST.get("email")
        supplier.phone = request.POST.get("phone")
        supplier.address = request.POST.get("address")
        supplier.is_active = (request.POST.get("is_active") == "True")
        supplier.save()
        return redirect("supplier_list")

    return render(request, "add_edit_supplier.html", {"supplier": supplier})


@login_required
def delete_supplier(request, supplier_id):
    supplier = get_object_or_404(Supplier, id=supplier_id)
    supplier.delete()
    return redirect("supplier_list")

# ---------------------------
# PRODUCT MANAGEMENT
# ---------------------------



@login_required
def product_list(request):
    products = Product.objects.select_related("category", "supplier").all()
    return render(request, "product_list.html", {"products": products})


@login_required
def add_product(request):
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Product added successfully!")
            return redirect("product_list")
    else:
        form = ProductForm()

    return render(request, "add_edit_product.html", {"form": form, "title": "Add New Product"})


@login_required
def edit_product(request, pk):
    product = get_object_or_404(Product, id=pk)

    if request.method == "POST":
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Product updated successfully!")
            return redirect("product_list")
    else:
        form = ProductForm(instance=product)

    return render(
        request,
        "add_edit_product.html",
        {"form": form, "title": f"Edit Product — {product.name}"}
    )


@login_required
def delete_product(request, pk):
    product = get_object_or_404(Product, id=pk)
    product.delete()
    messages.warning(request, "Product deleted!")
    return redirect("product_list")

# ---------------------------
# CATEGORY MANAGEMENT
# ---------------------------

def category_list(request):
    categories = Category.objects.all()
    return render(request, "category_list.html", {"categories": categories})


def add_category(request):
    if request.method == "POST":
        # save form
        pass
    return render(request, "category_form.html")


def edit_category(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == "POST":
        # save edited form
        pass
    return render(request, "category_form.html", {"category": category})


def delete_category(request, pk):
    category = get_object_or_404(Category, pk=pk)
    category.delete()
    return redirect("category_list")

# ---------------------------
# PURCHASE MANAGEMENT
# ---------------------------

@login_required
def purchase_list(request):
    q = request.GET.get("q", "")
    purchases = Purchase.objects.filter(supplier__name__icontains=q)
    return render(request, "purchase_list.html", {"purchases": purchases})


@login_required
def add_purchase(request):
    suppliers = Supplier.objects.all()

    if request.method == "POST":
        Purchase.objects.create(
            invoice_no=request.POST.get("invoice_no"),
            supplier_id=request.POST.get("supplier"),
            date=request.POST.get("date"),
            total_amount=request.POST.get("total_amount"),
            status=request.POST.get("status")
        )

        messages.success(request, "Purchase added successfully.")
        return redirect("purchase_list")

    return render(request, "add_edit_purchase.html", {"suppliers": suppliers})


@login_required
def edit_purchase(request, purchase_id):
    purchase = get_object_or_404(Purchase, id=purchase_id)
    suppliers = Supplier.objects.all()

    if request.method == "POST":
        purchase.invoice_no = request.POST.get("invoice_no")
        purchase.supplier_id = request.POST.get("supplier")
        purchase.date = request.POST.get("date")
        purchase.total_amount = request.POST.get("total_amount")
        purchase.status = request.POST.get("status")
        purchase.save()

        messages.success(request, "Purchase updated successfully.")
        return redirect("purchase_list")

    return render(request, "add_edit_purchase.html", {
        "purchase": purchase,
        "suppliers": suppliers
    })


@login_required
def delete_purchase(request, purchase_id):
    purchase = get_object_or_404(Purchase, id=purchase_id)
    purchase.delete()
    messages.success(request, "Purchase deleted successfully.")
    return redirect("purchase_list")

# ---------------------------
# SALES MANAGEMENT
# ---------------------------

@login_required
def sales_list(request):
    q = request.GET.get("q", "")
    sales = Sale.objects.filter(customer_name__icontains=q)
    return render(request, "sales_list.html", {"sales": sales})


@login_required
def add_sales(request):
    if request.method == "POST":
        Sale.objects.create(
            invoice_no=request.POST.get("invoice_no"),
            customer_name=request.POST.get("customer_name"),
            date=request.POST.get("date"),
            total_amount=request.POST.get("total_amount"),
            status=request.POST.get("status")
        )
        messages.success(request, "Sale added successfully.")
        return redirect("sales_list")

    return render(request, "add_edit_sales.html")


@login_required
def edit_sales(request, sales_id):
    sale = get_object_or_404(Sale, id=sales_id)

    if request.method == "POST":
        sale.invoice_no = request.POST.get("invoice_no")
        sale.customer_name = request.POST.get("customer_name")
        sale.date = request.POST.get("date")
        sale.total_amount = request.POST.get("total_amount")
        sale.status = request.POST.get("status")
        sale.save()

        messages.success(request, "Sale updated successfully.")
        return redirect("sales_list")

    return render(request, "add_edit_sales.html", {"sale": sale})


@login_required
def delete_sales(request, sales_id):
    sale = get_object_or_404(Sale, id=sales_id)
    sale.delete()
    messages.success(request, "Sale deleted successfully.")
    return redirect("sales_list")

# ---------------------------
# TRANSACTION SUMMARY
# ---------------------------

@login_required
def transactions(request):
    sale = Sale.objects.order_by("-date")
    purchases = Purchase.objects.order_by("-date")

    return render(
        request,
        "transaction.html",
        {"sale": sale, "purchases": purchases}
    )

# ---------------------------
# REPORTS
# ---------------------------

@login_required
def report_dashboard(request):
    total_products = Product.objects.count()
    total_categories = Category.objects.count()
    total_suppliers = Supplier.objects.count()
    low_stock = Product.objects.filter(stock__lt=10).count()

    category_breakdown = (
        Product.objects.values("category__name")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    return render(request, "report_dashboard.html", {
        "total_products": total_products,
        "total_categories": total_categories,
        "total_suppliers": total_suppliers,
        "low_stock": low_stock,
        "category_breakdown": category_breakdown
    })


@login_required
def stock_summary(request):
    by_category = (
        Product.objects.values("category__name")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    by_supplier = (
        Product.objects.values("supplier__name")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    return render(request, "stock_summary.html", {
        "by_category": by_category,
        "by_supplier": by_supplier
    })


def _get_safe(obj, attr, default=None):
    return getattr(obj, attr, default)


@login_required
def stock_report(request):
    qs = Product.objects.select_related("category").all()

    q = request.GET.get("q")
    if q:
        qs = qs.filter(name__icontains=q)

    category_id = request.GET.get("category")
    if category_id:
        qs = qs.filter(category_id=category_id)

    categories = Category.objects.all()

    rows = []
    for p in qs:
        rows.append({
            "id": p.id,
            "name": p.name,
            "category": getattr(p.category, "name", "—"),
            "supplier": getattr(_get_safe(p, "supplier"), "name", "—"),
            "sku": _get_safe(p, "sku", "—"),
            "price": _get_safe(p, "price", "—"),
            "cost_price": _get_safe(p, "cost_price", "—"),
            "quantity": _get_safe(p, "quantity", _get_safe(p, "stock", "—")),
            "reorder_level": _get_safe(p, "reorder_level", "—"),
            "updated_at": _get_safe(p, "updated_at", _get_safe(p, "modified", "—")),
        })

    return render(request, "stock_report.html", {
        "rows": rows,
        "categories": categories,
        "active_category": category_id,
        "query": q or "",
    })


@login_required
def stock_report_export_csv(request):
    qs = Product.objects.select_related("category").all()

    q = request.GET.get("q")
    if q:
        qs = qs.filter(name__icontains=q)

    category_id = request.GET.get("category")
    if category_id:
        qs = qs.filter(category_id=category_id)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="stock_report.csv"'
    writer = csv.writer(response)

    writer.writerow([
        "ID", "Name", "Category", "Supplier", "SKU",
        "Price", "Cost Price", "Quantity", "Reorder Level", "Updated At"
    ])

    for p in qs:
        writer.writerow([
            p.id,
            p.name,
            getattr(p.category, "name", ""),
            getattr(_get_safe(p, "supplier"), "name", ""),
            _get_safe(p, "sku", ""),
            _get_safe(p, "price", ""),
            _get_safe(p, "cost_price", ""),
            _get_safe(p, "quantity", _get_safe(p, "stock", "")),
            _get_safe(p, "reorder_level", ""),
            _get_safe(p, "updated_at", _get_safe(p, "modified", "")),
        ])

    return response

# ---------------------------
# SYSTEM SETTINGS
# ---------------------------

@login_required
def settings_view(request):
    return render(request, "settings.html")


def system_config(request):
    return render(request, "system_config.html")


def backup_restore(request):
    return render(request, "backup_restore.html")


def admin_logs(request):
    return render(request, "admin_logs.html")


def security_settings(request):
    return render(request, "security_settings.html")


def appearance_settings(request):
    return render(request, "appearance_settings.html")


@login_required
def user_home(request):
    context = {
        'product_count': Product.objects.count(),
        'purchase_count': Purchase.objects.count(),
        'sales_count': Sale.objects.count(),
    }
    return render(request, 'user_home.html', context)


@login_required
def user_product_list(request):
    products = Product.objects.all()
    return render(request, 'user_product_list.html', {'products': products})


@login_required
def user_product_detail(request, id):
    product = get_object_or_404(Product, id=id)
    return render(request, 'user_product_detail.html', {'product': product})


@login_required

def user_purchase_list(request):
    purchases = Purchase.objects.all()
    return render(request, "user_purchase_list.html", {"purchases": purchases})



@login_required
def user_sales_list(request):
    sales = Sale.objects.all()
    return render(request, "user_sales_list.html", {"sales": sales})




@login_required
def user_profile(request):
    return render(request, 'user_profile.html')


@login_required
def user_settings(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'user_settings.html', {'form': form})


@login_required
def user_reports(request):
    return render(request, 'user_reports.html')


def request_otp_view(request):
    if request.method == "POST":
        form = RequestOTPForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email'].strip().lower()
            try:
                user = User.objects.get(email__iexact=email)
            except User.DoesNotExist:
                # For security, still act like we sent an OTP
                messages.success(request, "If that email exists, an OTP has been sent.")
                return redirect('request-otp')
            # create OTP
            otp_obj = create_otp_for_user(user, ttl_minutes=10)
            try:
                send_otp_email(user, otp_obj)
            except Exception as e:
                # log e in real app
                messages.error(request, "Failed to send OTP. Try again later.")
                return redirect('request-otp')
            messages.success(request, "If that email exists, an OTP has been sent.")
            # redirect to OTP verify page — hide email in a hidden field or pass via GET
            return redirect(reverse('verify-otp') + f"?email={email}")
    else:
        form = RequestOTPForm()
    return render(request, 'app/request_otp.html', {'form': form})

def verify_otp_view(request):
    initial = {}
    if request.method == "GET":
        email = request.GET.get('email', '')
        initial['email'] = email
    if request.method == "POST":
        form = VerifyOTPForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email'].strip().lower()
            otp = form.cleaned_data['otp'].strip()
            try:
                user = User.objects.get(email__iexact=email)
            except User.DoesNotExist:
                messages.error(request, "Invalid OTP or email.")
                return redirect('verify-otp')
            # Look for latest unused OTP for this user
            try:
                otp_obj = PasswordResetOTP.objects.filter(user=user, used=False, otp=otp).order_by('-created_at').first()
            except PasswordResetOTP.DoesNotExist:
                otp_obj = None
            if not otp_obj:
                messages.error(request, "Invalid OTP.")
                return redirect('verify-otp')
            if otp_obj.is_expired():
                messages.error(request, "OTP expired. Request a new one.")
                return redirect('request-otp')
            # mark used to prevent reuse
            otp_obj.used = True
            otp_obj.save()
            # create a short-lived token or just redirect to reset password with user id in session
            request.session['password_reset_user_id'] = user.id
            # optional: set a flag that allows only password reset in next N minutes
            request.session['password_reset_allowed_at'] = timezone.now().isoformat()
            return redirect('reset-password')
    else:
        form = VerifyOTPForm(initial=initial)
    return render(request, 'app/verify_otp.html', {'form': form})

from django.contrib.auth import login

def reset_password_view(request):
    user_id = request.session.get('password_reset_user_id')
    if not user_id:
        messages.error(request, "No password reset session found. Start again.")
        return redirect('request-otp')
    user = get_object_or_404(User, pk=user_id)
    if request.method == "POST":
        form = ResetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            # cleanup session
            try:
                del request.session['password_reset_user_id']
                del request.session['password_reset_allowed_at']
            except KeyError:
                pass
            messages.success(request, "Password updated successfully. You can now log in.")
            return redirect('login')  # change to your login url name
    else:
        form = ResetPasswordForm(user)
    return render(request, 'app/reset_password.html', {'form': form})
