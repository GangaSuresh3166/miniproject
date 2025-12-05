# app/utils.py
import random, uuid
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.core.mail import send_mail
from .models import PasswordResetOTP


def generate_numeric_otp(length=6):
    # ensure leading zeros allowed
    return ''.join(str(random.randint(0,9)) for _ in range(length))


def generate_transaction_no():
    return f"TRX-{uuid.uuid4().hex[:8].upper()}"


def create_otp_for_user(user, ttl_minutes=10):
    otp = f"{random.randint(100000, 999999)}"
    expires_at = timezone.now() + timedelta(minutes=ttl_minutes)

    otp_obj = PasswordResetOTP.objects.create(
        user=user,
        otp=otp,
        expires_at=expires_at
    )

    return otp_obj


def send_otp_email(user, otp_obj):
    subject = "Your Password Reset OTP"
    message = f"""
Hello {user.username},

Your OTP for password reset is: {otp_obj.otp}

This OTP will expire in 10 minutes.

Thank you.
"""

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False
    )

