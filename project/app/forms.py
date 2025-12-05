from django import forms
from django.contrib.auth import get_user_model
from django.forms import inlineformset_factory, BaseInlineFormSet
from django.contrib.auth.forms import UserCreationForm, SetPasswordForm
from django.utils import timezone
from .models import (
    Supplier, Product, Category, SubCategory,
    Purchase, PurchaseItem,Sales, SalesItem,SystemConfig, SystemLog, AppearanceSettings)
from .models import Product, Category, SubCategory, Supplier
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.forms import modelformset_factory

User = get_user_model()


class UserForm(forms.ModelForm):
    # Password field (for creating users only)
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        required=False,
        help_text="Leave blank to keep current password",
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "phone",
            "password",
            "is_active",
            "is_staff",
        ]

        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_staff": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)

        pwd = self.cleaned_data.get("password")
        if pwd:
            user.set_password(pwd)  # Hash password

        if commit:
            user.save()
        return user


# ============================================
# CATEGORY / SUBCATEGORY / PRODUCT FORMS
# ============================================

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["category_name", "is_active"]

        widgets = {
            "category_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter category name"
            }),
            "is_active": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            }),
        }


# ============================
# SUBCATEGORY FORM
# ============================
class SubCategoryForm(forms.ModelForm):
    class Meta:
        model = SubCategory
        fields = ["subcategory_name", "is_active"]

        widgets = {
            "subcategory_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter subcategory name"
            }),
            "is_active": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            }),
        }


# ===== Correct & Final Formset =====
SubCategoryFormSet = modelformset_factory(
    SubCategory,
    form=SubCategoryForm,
    extra=1,            # 1 empty row
    can_delete=True,    # allow deletion
)


# ============================================
# PRODUCT FORM
# ============================================

class ProductForm(forms.ModelForm):

    class Meta:
        model = Product
        fields = [
            "product_id",
            "name",
            "category",
            "subcategory",
            "brand",
            "description",
            "cost_price",
            "selling_price",
            "discount",
            "tax",
            "quantity",
            "reorder_level",
            "supplier_name",
            "supplier_contact",
            "status",
            "notes",
        ]
        widgets = {
            "product_id": forms.TextInput(attrs={"class": "form-control"}),
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "category": forms.Select(attrs={"class": "form-control", "onchange": "this.form.submit()"}),
            "subcategory": forms.Select(attrs={"class": "form-control"}),

            "brand": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),

            "cost_price": forms.NumberInput(attrs={"class": "form-control"}),
            "selling_price": forms.NumberInput(attrs={"class": "form-control"}),
            "discount": forms.NumberInput(attrs={"class": "form-control"}),
            "tax": forms.NumberInput(attrs={"class": "form-control"}),

            "quantity": forms.NumberInput(attrs={"class": "form-control"}),
            "reorder_level": forms.NumberInput(attrs={"class": "form-control"}),

            "supplier_name": forms.TextInput(attrs={"class": "form-control"}),
            "supplier_contact": forms.TextInput(attrs={"class": "form-control"}),

            "status": forms.Select(attrs={"class": "form-control"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # default empty
        self.fields["subcategory"].queryset = SubCategory.objects.none()

        # Case 1: POST
        if "category" in self.data:
            try:
                category_id = int(self.data.get("category"))
                self.fields["subcategory"].queryset = SubCategory.objects.filter(category_id=category_id)
            except (ValueError, TypeError):
                pass

        # Case 2: Edit mode
        elif self.instance.pk and self.instance.category:
            self.fields["subcategory"].queryset = SubCategory.objects.filter(category=self.instance.category)


# ============================================
# SUPPLIER FORM
# ============================================

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = "__all__"
        widgets = {
            'supplier_name': forms.TextInput(attrs={'class': 'form-control'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'alt_phone': forms.TextInput(attrs={'class': 'form-control'}),

            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),

            'gst_number': forms.TextInput(attrs={'class': 'form-control'}),
            'pan_number': forms.TextInput(attrs={'class': 'form-control'}),

            'bank_name': forms.TextInput(attrs={'class': 'form-control'}),
            'account_number': forms.TextInput(attrs={'class': 'form-control'}),
            'ifsc_code': forms.TextInput(attrs={'class': 'form-control'}),
            'branch': forms.TextInput(attrs={'class': 'form-control'}),

            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


# ============================================
# PURCHASE FORMS + FORMSET
# ============================================

class PurchaseForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = "__all__"
        widgets = {
            # top section
            "purchase_no": forms.TextInput(attrs={"class": "form-control"}),
            "date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),

            "payment_type": forms.Select(attrs={"class": "form-select"}),
            "supplier": forms.Select(attrs={"class": "form-select"}),

            # totals section
            "subtotal": forms.NumberInput(attrs={"class": "form-control", "readonly": "readonly"}),
            "discount_total": forms.NumberInput(attrs={"class": "form-control"}),
            "tax_total": forms.NumberInput(attrs={"class": "form-control"}),
            "other_charges": forms.NumberInput(attrs={"class": "form-control"}),
            "grand_total": forms.NumberInput(attrs={"class": "form-control", "readonly": "readonly"}),
            "amount_paid": forms.NumberInput(attrs={"class": "form-control"}),
            "balance": forms.NumberInput(attrs={"class": "form-control", "readonly": "readonly"}),
            "payment_status": forms.Select(attrs={"class": "form-select"}),

            # notes
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class PurchaseItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseItem
        fields = ["product", "qty", "unit_price", "discount", "tax", "line_total"]

PurchaseItemFormSet = forms.inlineformset_factory(
    parent_model=Purchase,
    model=PurchaseItem,
    form=PurchaseItemForm,
    extra=0,
    can_delete=True
)

# =====================================================
# SALES ITEM FORM
# =====================================================

class SalesForm(forms.ModelForm):
    class Meta:
        model = Sales
        fields = [
            "invoice_no",
            "customer_name",
            "date",
            "payment_status",
            "notes",
        ]

        widgets = {
            "invoice_no": forms.TextInput(attrs={"class": "form-control", "readonly": True}),
            "customer_name": forms.TextInput(attrs={"class": "form-control"}),
            "date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "payment_status": forms.Select(attrs={"class": "form-select"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

class SalesItemForm(forms.ModelForm):
    class Meta:
        model = SalesItem
        fields = ["product", "qty", "price", "discount", "tax", "total"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Make total readonly (calculated in JS)
        self.fields["total"].widget.attrs["readonly"] = True

        # Optional: product selector nice style
        self.fields["product"].widget.attrs.update({"class": "form-select"})


SalesItemFormset = inlineformset_factory(
    Sales,
    SalesItem,
    form=SalesItemForm,
    extra=1,
    can_delete=True
)


# ============================================
# SYSTEM FORMS (NO timestamp field!)
# ============================================

class SystemConfigForm(forms.ModelForm):
    class Meta:
        model = SystemConfig
        fields = ["system_name", "currency", "default_tax"]

class SystemLogForm(forms.ModelForm):
    class Meta:
        model = SystemLog
        exclude = "__all__"   



class AppearanceSettingsForm(forms.ModelForm):
    class Meta:
        model = AppearanceSettings
        fields = ["theme"]


# ============================================
# OTP / PASSWORD RESET FORMS
# ============================================

class RequestOTPForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": "form-control"})
    )


class VerifyOTPForm(forms.Form):
    email = forms.EmailField(widget=forms.HiddenInput())
    otp = forms.CharField(
        max_length=6,
        widget=forms.TextInput(attrs={"class": "form-control"})
    )


class ResetPasswordForm(SetPasswordForm):
    """Uses Django's built-in secure reset form."""
    pass
