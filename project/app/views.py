from datetime import timedelta
import random ,csv ,json ,os
from io import BytesIO
from django.views import View
from django.db.models import Sum
from .forms import SubCategoryFormSet
from .forms import SalesItemFormset
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, path
from django.template.response import TemplateResponse
from django.contrib import messages, admin
from django.contrib.auth import (
    authenticate, login, logout, update_session_auth_hash, get_user_model
)
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import PasswordChangeForm
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from django.contrib.admin.models import LogEntry
try:
    import openpyxl
    from openpyxl.styles import Font
except Exception:
    openpyxl = None

# Local imports
from .models import (
    Supplier, Product, Category, SubCategory,
    Purchase, PurchaseItem,Sales, SalesItem,Customer,LoginOTP, PasswordResetOTP
)
from django.forms import inlineformset_factory
from .forms import (
    RequestOTPForm, VerifyOTPForm, ResetPasswordForm, SubCategoryForm,
    UserForm, ProductForm, SupplierForm, CategoryForm,PurchaseForm, PurchaseItemFormSet,
    SalesForm, SalesItemForm
)
from .utils import create_otp_for_user, send_otp_email, generate_transaction_no

User = get_user_model()


# ---------------------------
# Helper utilities
# ---------------------------

def admin_only(user):
    return user.is_superuser


def calc_purchase_totals_from_formset(formset):
    """Return subtotal computed by formset if set by BasePurchaseItemFormSet."""
    return getattr(formset, "subtotal", 0)


def compute_grand_and_balance(subtotal, discount_total, tax_total, other_charges, amount_paid):
    subtotal = subtotal or 0
    discount_total = discount_total or 0
    tax_total = tax_total or 0
    other_charges = other_charges or 0
    amount_paid = amount_paid or 0

    grand_total = subtotal - discount_total + tax_total + other_charges
    balance = max(grand_total - amount_paid, 0)
    return grand_total, balance


# ---------------------------
# AUTH: login / logout
# ---------------------------

def index(request):
    return render(request, "index.html")


def login_view(request):
    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        password = (request.POST.get("password") or "").strip()
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            if user.is_superuser:
                return redirect("admin_home")
            if user.is_staff:
                return redirect("user_home")
            messages.error(request, "Unauthorized access.")
            return redirect("login")
        messages.error(request, "Invalid username or password.")
        return redirect("login")
    return render(request, "login.html")


def logout_view(request):
    logout(request)
    return redirect("login")


# ---------------------------
# OTP AUTH (login) helpers
# ---------------------------

def _create_and_store_login_otp(user, minutes=10):
    code = f"{random.randint(0, 999999):06d}"
    expires_at = timezone.now() + timedelta(minutes=minutes)
    otp = LoginOTP.objects.create(user=user, code=code, expires_at=expires_at)
    return otp


def otp_request(request):
    """Request login OTP via username or email."""
    if request.method == "POST":
        identifier = (request.POST.get("identifier") or "").strip()
        user = None
        if "@" in identifier:
            user = User.objects.filter(email__iexact=identifier).first()
        else:
            user = User.objects.filter(username__iexact=identifier).first()

        if not user:
            messages.error(request, "User not found")
            return render(request, "otp_request.html")

        _create_and_store_login_otp(user)
        request.session["otp_uid"] = user.id
        messages.success(request, "OTP sent (development: check database).")
        return redirect("otp_verify")

    return render(request, "otp_request.html")


def otp_verify(request):
    uid = request.session.get("otp_uid")
    if not uid:
        return redirect("otp_request")
    user = get_object_or_404(User, id=uid)

    if request.method == "POST":
        code = (request.POST.get("code") or "").strip()
        otp = LoginOTP.objects.filter(user=user, used=False).order_by("-created_at").first()
        if not otp or not otp.is_valid() or otp.code != code:
            messages.error(request, "Invalid or expired OTP.")
            return redirect("otp_request")
        otp.used = True
        otp.save()
        login(request, user)
        return redirect("admin_home")
    return render(request, "otp_verify.html", {"user": user})

# ---------------------------
# Dashboard
# ---------------------------

@login_required
@login_required
def admin_home(request):
    from django.db.models import Sum
    from .models import Sales, Purchase

    # ======== YOUR OLD METRICS ========
    total_users = User.objects.filter(is_superuser=False).count()
    total_suppliers = Supplier.objects.count()
    total_products = Product.objects.count()

    # ======== NEW ANALYTICS DATA ========
    # Group Sales by date
    sales = (
        Sales.objects.values("date")
        .annotate(total=Sum("grand_total"))
        .order_by("date")
    )

    # Group Purchases by date
    purchases = (
        Purchase.objects.values("date")
        .annotate(total=Sum("grand_total"))
        .order_by("date")
    )

    # Convert to Chart.js format
    sales_labels = [s["date"].strftime("%Y-%m-%d") for s in sales]
    sales_values = [float(s["total"]) for s in sales]

    purchase_values = [float(p["total"]) for p in purchases]

    return render(request, "admin_home.html", {
        "total_users": total_users,
        "total_suppliers": total_suppliers,
        "total_products": total_products,

        # chart data
        "sales_labels": sales_labels,
        "sales_values": sales_values,
        "purchase_values": purchase_values,
    })


# ---------------------------
# User Management (admin)
# ---------------------------

@user_passes_test(admin_only)
@login_required
def users_list(request):
    users = User.objects.filter(is_staff=True, is_superuser=False).order_by("username")
    return render(request, "users_list.html", {"users": users})


@user_passes_test(admin_only)
@login_required
def add_user(request):
    form = UserForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            user = form.save(commit=False)
            user.is_staff = True
            user.save()
            messages.success(request, "Staff added successfully.")
            return redirect("users_list")
        messages.error(request, "Please fix the errors below.")
    return render(request, "user_add_edit.html", {"form": form})


@user_passes_test(admin_only)
@login_required
def edit_user(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)
    form = UserForm(request.POST or None, instance=user_obj)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Staff updated successfully.")
            return redirect("users_list")
        messages.error(request, "Please fix the errors below.")
    return render(request, "user_add_edit.html", {"form": form, "user": user_obj})


@user_passes_test(admin_only)
@login_required
def delete_user(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)
    if request.method == "POST":
        user_obj.delete()
        messages.success(request, "Staff deleted.")
        return redirect("users_list")
    return render(request, "confirm_delete.html", {"user": user_obj})


# ---------------------------
# Supplier CRUD
# ---------------------------

@login_required
def supplier_list(request):
    suppliers = Supplier.objects.all()
    return render(request, "supplier_list.html", {"suppliers": suppliers})


@login_required
def supplier_add(request):
    form = SupplierForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Supplier added successfully!")
            return redirect("supplier_list")
        messages.error(request, "Please correct the errors below.")
    return render(request, "supplier_add_edit.html", {"form": form, "title": "Add Supplier"})


@login_required
def supplier_edit(request, supplier_id):
    supplier = get_object_or_404(Supplier, id=supplier_id)
    form = SupplierForm(request.POST or None, instance=supplier)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Supplier updated successfully!")
            return redirect("supplier_list")
        messages.error(request, "Please correct the errors below.")
    return render(request, "supplier_add_edit.html", {"form": form, "title": "Edit Supplier", "supplier": supplier})


@login_required
def supplier_delete(request, supplier_id):
    supplier = get_object_or_404(Supplier, id=supplier_id)
    if request.method == "POST":
        supplier.delete()
        messages.success(request, "Supplier deleted successfully!")
        return redirect("supplier_list")
    return render(request, "supplier_confirm_delete.html", {"supplier": supplier})


# ---------------------------
# Category / SubCategory
# ---------------------------

login_required
def category_list(request):
    categories = Category.objects.all().order_by("category_name")
    return render(request, "category_list.html", {
        "categories": categories,
        "title": "Category List",
    })

@login_required
def category_add(request):
    if request.method == "POST":
        form = CategoryForm(request.POST)
        formset = SubCategoryFormSet(
            request.POST,
            queryset=SubCategory.objects.none()
        )

        if form.is_valid() and formset.is_valid():
            category = form.save()

            # Save all subcategories
            subcats = formset.save(commit=False)
            for sub in subcats:
                sub.category = category
                sub.save()

            messages.success(request, "Category & Subcategories added successfully.")
            return redirect("category_list")

        else:
            messages.error(request, "Please fix the errors below.")

    else:
        form = CategoryForm()
        formset = SubCategoryFormSet(queryset=SubCategory.objects.none())

    return render(request, "category_add_edit.html", {
        "form": form,
        "formset": formset,
        "title": "Add Category",
    })

@login_required
def category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)

    if request.method == "POST":
        form = CategoryForm(request.POST, instance=category)
        formset = SubCategoryFormSet(
            request.POST,
            queryset=SubCategory.objects.filter(category=category)
        )

        if form.is_valid() and formset.is_valid():
            form.save()

            # Save existing + new subcategories
            subcats = formset.save(commit=False)

            for sub in subcats:
                sub.category = category
                sub.save()

            # Delete removed subcategories
            for deleted in formset.deleted_objects:
                deleted.delete()

            messages.success(request, "Category & Subcategories updated successfully.")
            return redirect("category_list")
        else:
            messages.error(request, "Please correct the errors below.")

    else:
        form = CategoryForm(instance=category)
        formset = SubCategoryFormSet(
            queryset=SubCategory.objects.filter(category=category)
        )

    return render(request, "category_add_edit.html", {
        "form": form,
        "formset": formset,
        "title": "Edit Category",
    })

def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)

    if request.method == "POST":
        category.delete()
        return redirect("category_list")

    return render(request, "category_delete_confirm.html", {"category": category})


@login_required
def subcategory_list(request):
    subcats = SubCategory.objects.select_related("category").all()
    return render(request, "subcategory_list.html", {"data": subcats})


@login_required
def subcategory_add(request):
    form = SubCategoryForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Sub-category added.")
            return redirect("subcategory_list")
        messages.error(request, "Please fix the errors.")
    return render(request, "subcategory_form.html", {"form": form, "title": "Add Sub-Category"})


@login_required
def subcategory_edit(request, pk):
    subcat = get_object_or_404(SubCategory, pk=pk)
    form = SubCategoryForm(request.POST or None, instance=subcat)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Sub-category updated.")
            return redirect("subcategory_list")
        messages.error(request, "Please fix the errors.")
    return render(request, "subcategory_form.html", {"form": form, "title": "Edit Sub-Category", "subcat": subcat})


@login_required
def subcategory_delete(request, pk):
    subcat = get_object_or_404(SubCategory, pk=pk)
    if request.method == "POST":
        subcat.delete()
        messages.success(request, "Sub-category deleted.")
        return redirect("subcategory_list")
    return render(request, "subcategory_delete_confirm.html", {"subcat": subcat})


# ---------------------------
# Product CRUD & Ajax
# ---------------------------

@login_required
def product_list(request):
    products = Product.objects.select_related("category", "subcategory").all()
    return render(request, "product_list.html", {"products": products})


@login_required
def product_add(request):
    if request.method == "POST":
        form = ProductForm(request.POST)

        # Auto-submit when category is changed
        if request.POST.get("category_changed") == "1":
            return render(request, "product_add_edit.html", {"form": form})

        # Normal save
        if form.is_valid():
            form.save()
            return redirect("product_list")

    else:
        form = ProductForm()

    return render(request, "product_add_edit.html", {"form": form})


def get_subcategories(request):
    category_id = request.GET.get("category_id")
    subcats = SubCategory.objects.filter(category_id=category_id)

    data = [{"id": s.id, "name": s.name} for s in subcats]
    return JsonResponse({"SubCategories": data})



@login_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form = ProductForm(request.POST or None, instance=product)
    subcategories = SubCategory.objects.all()

    return render(request, "product_add_edit.html", {
        "form": form,
        "subcategories": subcategories,
    })


@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        product.delete()
        messages.success(request, "Product deleted.")
        return redirect("product_list")
    return render(request, "product_confirm_delete.html", {"product": product})


# ---------------------------
# Purchases (list, add, edit, delete)
# ---------------------------
def purchase_list(request):
    search = request.GET.get("search", "")

    purchases = Purchase.objects.all().order_by("-id")

    if search:
        purchases = purchases.filter(invoice_number__icontains=search)

    context = {
        "title": "Purchase List",
        "purchases": purchases,
        "search": search,
    }
    return render(request, "purchase_list.html", context)

@transaction.atomic
@login_required

def supplier_detail_json(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    data = {
        "id": supplier.id,
        "supplier_name": supplier.supplier_name,
        "company_name": supplier.company_name,
        "email": supplier.email,
        "phone": supplier.phone,
        "alt_phone": supplier.alt_phone,
        "gst_number": supplier.gst_number,
        "pan_number": supplier.pan_number,
        "address": supplier.address,
        "city": supplier.city,
        "state": supplier.state,
        "country": supplier.country,
        "postal_code": supplier.postal_code
    }
    return JsonResponse(data)


def product_detail_json(request, pk):
    product = get_object_or_404(Product, pk=pk)
    data = {
        "id": product.id,
        "product_id": product.product_id,
        "name": product.name,
        "cost_price": str(product.cost_price or 0),
        "selling_price": str(product.selling_price or 0),
        "discount": str(product.discount or 0),
        "tax": str(product.tax or 0),
    }
    return JsonResponse(data)


def purchase_add(request):

    if request.method == 'POST':
        form = PurchaseForm(request.POST)

        if form.is_valid():
            purchase = form.save()                     # Save purchase
            create_purchase_transaction(purchase)      # Auto-generate transaction
            return redirect('purchase_list')

    else:
        form = PurchaseForm()

    products = Product.objects.filter(status='active').order_by('name')
    suppliers = Supplier.objects.all().order_by('supplier_name')

    return render(request, 'purchase_add_edit.html', {
        'form': form,
        'products': products,
        'suppliers': suppliers,
    })


@transaction.atomic
@login_required
def purchase_edit(request, pk):
    purchase = get_object_or_404(Purchase, pk=pk)
    if request.method == "POST":
        form = PurchaseForm(request.POST, instance=purchase)
        formset = PurchaseItemFormSet(request.POST, instance=purchase)
        if form.is_valid() and formset.is_valid():
            purchase_obj = form.save(commit=False)

            subtotal = calc_purchase_totals_from_formset(formset)
            purchase_obj.subtotal = subtotal

            grand_total, balance = compute_grand_and_balance(
                subtotal,
                purchase_obj.discount_total,
                purchase_obj.tax_total,
                purchase_obj.other_charges,
                purchase_obj.amount_paid
            )
            purchase_obj.grand_total = grand_total
            purchase_obj.balance = balance

            purchase_obj.save()
            formset.save()
            messages.success(request, "Purchase updated successfully.")
            return redirect("purchase_list")

        messages.error(request, "Please fix the errors below.")
    else:
        form = PurchaseForm(instance=purchase)
        formset = PurchaseItemFormSet(instance=purchase)

    return render(request, "purchase_add_edit.html", {"form": form, "formset": formset, "title": "Edit Purchase"})


@transaction.atomic
@login_required
def purchase_delete(request, pk):
    purchase = get_object_or_404(Purchase, pk=pk)
    if request.method == "POST":
        purchase.delete()
        messages.success(request, "Purchase deleted.")
        return redirect("purchase_list")
    return render(request, "purchase_confirm_delete.html", {"purchase": purchase})

#----------------------------
# sales
#----------------------------

from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.contrib.auth.decorators import login_required
from .models import Sales, SalesItem, Product
from .forms import SalesForm, SalesItemFormset
from django.http import HttpResponse

def generate_invoice_no():
    last_sale = Sales.objects.order_by("id").last()
    if not last_sale:
        return "INV-0001"
    try:
        last_no = int(last_sale.invoice_no.split("-")[1])
    except Exception:
        last_no = last_sale.id
    return f"INV-{last_no + 1:04d}"

@login_required
def sales_list(request):
    sales = Sales.objects.all().order_by("-id")
    return render(request, "sales_list.html", {"sales": sales})


@login_required
@transaction.atomic
def sales_add(request):
    if request.method == "POST":

        customer_name = request.POST.get("customer_name")
        date = request.POST.get("date")

        subtotal = float(request.POST.get("subtotal") or 0)
        totaltax = float(request.POST.get("totaltax") or 0)
        grandtotal = float(request.POST.get("grandtotal") or 0)

        # create sale
        sale = Sales.objects.create(
            invoice_no = generate_invoice_no(),
            customer_name = customer_name,
            date = date,
            subtotal = subtotal,
            total_tax = totaltax,
            grand_total = grandtotal,
        )

        # get item lists
        products = request.POST.getlist("product[]")
        qtys = request.POST.getlist("qty[]")
        prices = request.POST.getlist("price[]")
        discounts = request.POST.getlist("discount[]")
        taxes = request.POST.getlist("tax[]")
        totals = request.POST.getlist("total[]")

        # loop through rows
        for p, q, pr, d, t, tot in zip(products, qtys, prices, discounts, taxes, totals):
            if p == "":
                continue  # skip empty rows

            product = Product.objects.get(id=p)

            SalesItem.objects.create(
                sale=sale,
                product=product,
                qty=int(q or 0),
                price=float(pr or 0),
                discount=float(d or 0),
                tax=float(t or 0),
                total=float(tot or 0),
            )

            # update stock
            product.quantity -= int(q)
            product.save()

        # 🔥 AUTO CREATE SALE ACCOUNTING TRANSACTION
        create_sales_transaction(sale)

        return redirect("sales_list")

    # GET request
    return render(request, "sales_add_edit.html", {
        "products": Product.objects.all(),
        "today": timezone.now().date(),
    })


def sales_edit(request, pk):
    sale = Sales.objects.get(id=pk)
    items = sale.items.all()

    if request.method == "POST":
        # Same saving structure as sales_add
        customer_name = request.POST.get("customer_name")
        date = request.POST.get("date")

        subtotal = request.POST.get("subtotal") or 0
        totaltax = request.POST.get("totaltax") or 0
        grandtotal = request.POST.get("grandtotal") or 0

        # Update sale
        sale.customer_name = customer_name
        sale.date = date
        sale.subtotal = subtotal
        sale.total_tax = totaltax
        sale.grand_total = grandtotal
        sale.save()

        # Delete old items (clean update)
        sale.items.all().delete()

        # Recreate item rows
        products = request.POST.getlist("product[]")
        qtys = request.POST.getlist("qty[]")
        prices = request.POST.getlist("price[]")
        discounts = request.POST.getlist("discount[]")
        taxes = request.POST.getlist("tax[]")
        totals = request.POST.getlist("total[]")

        for p, q, pr, d, t, tot in zip(products, qtys, prices, discounts, taxes, totals):
            if p == "":
                continue

            product = Product.objects.get(id=p)

            SalesItem.objects.create(
                sale=sale,
                product=product,
                qty=q,
                price=pr,
                discount=d,
                tax=t,
                total=tot,
            )

        return redirect("sales_list")

    return render(request, "sales_add_edit.html", {
        "edit_mode": True,
        "sale": sale,
        "items": items,
        "products": Product.objects.all(),
        "today": sale.date,
    })



@login_required
@transaction.atomic
def sales_delete(request, pk):
    sale = get_object_or_404(Sales, pk=pk)

    # restore stock before deleting
    for item in sale.items.all():
        product = item.product
        product.quantity += item.qty
        product.save()

    sale.delete()
    messages.success(request, "Sale deleted successfully.")
    return redirect("sales_list")


# ---------------------------
# Admin logs (kept here by request)
# ---------------------------

def logs_view(request):
    logs = LogEntry.objects.select_related("user", "content_type").order_by("-action_time")[:500]
    context = dict(admin.site.each_context(request))
    context.update({"logs": logs, "title": "Admin Activity Logs"})
    return TemplateResponse(request, "admin_logs.html", context)


def _get_admin_urls(orig_get_urls):
    def get_urls():
        custom_urls = [path("logs/", admin.site.admin_view(logs_view), name="admin_logs")]
        return custom_urls + orig_get_urls()
    return get_urls

# patch admin urls (kept per your earlier request)
admin.site.get_urls = _get_admin_urls(admin.site.get_urls)


@login_required
@login_required
def user_home(request):
    return render(request, 'user_home.html')


@login_required
def user_sales_list(request):
    sales = Sales.objects.all().order_by("-id")
    return render(request, "user_sales_list.html", {"sales": sales})


@login_required
@transaction.atomic
def user_sales_add(request):
    if request.method == "POST":

        customer_name = request.POST.get("customer_name")
        date = request.POST.get("date")

        subtotal = float(request.POST.get("subtotal") or 0)
        totaltax = float(request.POST.get("totaltax") or 0)
        grandtotal = float(request.POST.get("grandtotal") or 0)

        # create sale
        sale = Sales.objects.create(
            invoice_no = generate_invoice_no(),
            customer_name = customer_name,
            date = date,
            subtotal = subtotal,
            total_tax = totaltax,
            grand_total = grandtotal,
        )

        # get item lists
        products = request.POST.getlist("product[]")
        qtys = request.POST.getlist("qty[]")
        prices = request.POST.getlist("price[]")
        discounts = request.POST.getlist("discount[]")
        taxes = request.POST.getlist("tax[]")
        totals = request.POST.getlist("total[]")

        # loop through rows
        for p, q, pr, d, t, tot in zip(products, qtys, prices, discounts, taxes, totals):
            if p == "":
                continue  # skip empty rows

            product = Product.objects.get(id=p)

            SalesItem.objects.create(
                sale=sale,
                product=product,
                qty=int(q or 0),
                price=float(pr or 0),
                discount=float(d or 0),
                tax=float(t or 0),
                total=float(tot or 0),
            )

            # update stock
            product.quantity -= int(q)
            product.save()

        # 🔥 AUTO CREATE SALE ACCOUNTING TRANSACTION
        create_sales_transaction(sale)

        return redirect("sales_list")

    # GET request
    return render(request, "user_sales_form.html", {
        "products": Product.objects.all(),
        "today": timezone.now().date(),
    })


def user_sales_edit(request, pk):
    sale = Sales.objects.get(id=pk)
    items = sale.items.all()

    if request.method == "POST":
        # Same saving structure as sales_add
        customer_name = request.POST.get("customer_name")
        date = request.POST.get("date")

        subtotal = request.POST.get("subtotal") or 0
        totaltax = request.POST.get("totaltax") or 0
        grandtotal = request.POST.get("grandtotal") or 0

        # Update sale
        sale.customer_name = customer_name
        sale.date = date
        sale.subtotal = subtotal
        sale.total_tax = totaltax
        sale.grand_total = grandtotal
        sale.save()

        # Delete old items (clean update)
        sale.items.all().delete()

        # Recreate item rows
        products = request.POST.getlist("product[]")
        qtys = request.POST.getlist("qty[]")
        prices = request.POST.getlist("price[]")
        discounts = request.POST.getlist("discount[]")
        taxes = request.POST.getlist("tax[]")
        totals = request.POST.getlist("total[]")

        for p, q, pr, d, t, tot in zip(products, qtys, prices, discounts, taxes, totals):
            if p == "":
                continue

            product = Product.objects.get(id=p)

            SalesItem.objects.create(
                sale=sale,
                product=product,
                qty=q,
                price=pr,
                discount=d,
                tax=t,
                total=tot,
            )

        return redirect("user_sales_list")

    return render(request, "user_sales_form.html", {
        "edit_mode": True,
        "sale": sale,
        "items": items,
        "products": Product.objects.all(),
        "today": sale.date,
    })



@login_required
@transaction.atomic
def user_sales_delete(request, pk):
    sale = get_object_or_404(Sales, pk=pk)

    # restore stock before deleting
    for item in sale.items.all():
        product = item.product
        product.quantity += item.qty
        product.save()

    sale.delete()
    messages.success(request, "Sale deleted successfully.")
    return redirect("user_sales_list")

# ---------------------------
# Password reset via OTP (request, verify, reset)
# ---------------------------

def request_otp_view(request):
    if request.method == "POST":
        form = RequestOTPForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"].strip().lower()
            try:
                user = User.objects.get(email__iexact=email)
            except User.DoesNotExist:
                messages.success(request, "If that email exists, an OTP has been sent.")
                return redirect("request_otp")
            otp_obj = create_otp_for_user(user, ttl_minutes=10)
            try:
                send_otp_email(user, otp_obj)
            except Exception:
                messages.error(request, "Failed to send OTP. Try again later.")
                return redirect("request_otp")
            messages.success(request, "If that email exists, an OTP has been sent.")
            return redirect(reverse("verify_otp") + f"?email={email}")
    else:
        form = RequestOTPForm()
    return render(request, "request_otp.html", {"form": form})


def verify_otp_view(request):
    initial = {}
    email = ""
    if request.method == "GET":
        email = request.GET.get("email", "")
        initial["email"] = email
    if request.method == "POST":
        form = VerifyOTPForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"].strip().lower()
            otp = form.cleaned_data["otp"].strip()
            try:
                user = User.objects.get(email__iexact=email)
            except User.DoesNotExist:
                messages.error(request, "Invalid OTP or email.")
                return redirect("verify_otp")
            otp_obj = PasswordResetOTP.objects.filter(user=user, used=False, otp=otp).order_by("-created_at").first()
            if not otp_obj:
                messages.error(request, "Invalid OTP.")
                return redirect("verify_otp")
            if otp_obj.is_expired():
                messages.error(request, "OTP expired. Request a new one.")
                return redirect("request_otp")
            otp_obj.used = True
            otp_obj.save()
            request.session["password_reset_user_id"] = user.id
            request.session["password_reset_allowed_at"] = timezone.now().isoformat()
            return redirect("reset_password")
        messages.error(request, "Invalid data.")
    else:
        form = VerifyOTPForm(initial=initial)
    return render(request, "verify_otp.html", {"form": form, "email": email})


def reset_password_view(request):
    user_id = request.session.get("password_reset_user_id")
    if not user_id:
        messages.error(request, "No password reset session found. Start again.")
        return redirect("request_otp")
    user = get_object_or_404(User, pk=user_id)
    if request.method == "POST":
        form = ResetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            # cleanup session
            request.session.pop("password_reset_user_id", None)
            request.session.pop("password_reset_allowed_at", None)
            messages.success(request, "Password updated successfully. You can now log in.")
            return redirect("login")
        messages.error(request, "Please fix the errors.")
    else:
        form = ResetPasswordForm(user)
    return render(request, "reset_password_otp.html", {"form": form})




import json
from django.db.models import Sum
from django.shortcuts import render
from .models import Sales, Purchase


def analytics_view(request):
    # Aggregate sales grouped by date
    sales_data = (
        Sales.objects.values("date")
        .annotate(total=Sum("grand_total"))
        .order_by("date")
    )

    # Aggregate purchases grouped by date
    purchase_data = (
        Purchase.objects.values("date")
        .annotate(total=Sum("grand_total"))
        .order_by("date")
    )

    # Convert queryset → Python lists
    sales_labels = [s["date"].strftime("%Y-%m-%d") for s in sales_data]
    sales_totals = [float(s["total"]) for s in sales_data]

    purchase_labels = [p["date"].strftime("%Y-%m-%d") for p in purchase_data]
    purchase_totals = [float(p["total"]) for p in purchase_data]

    # Convert Python lists → JSON (this is required for Chart.js)
    context = {
        "sales_labels": json.dumps(sales_labels),
        "sales_totals": json.dumps(sales_totals),
        "purchase_labels": json.dumps(purchase_labels),
        "purchase_totals": json.dumps(purchase_totals),
    }

    return render(request, "analytics.html", context)



def user_profile(request):
    user = request.user
    return render(request, "user_profile.html", {"user": user})

from django.contrib import messages

@login_required
def edit_profile(request):
    user = request.user

    if request.method == "POST":
        user.username = request.POST.get("username")
        user.first_name = request.POST.get("first_name")
        user.last_name = request.POST.get("last_name")
        user.email = request.POST.get("email")
        user.phone = request.POST.get("phone")
        user.save()

        messages.success(request, "Profile updated successfully!")
        return redirect("user_profile")

    return render(request, "edit_profile.html", {"user": user})
