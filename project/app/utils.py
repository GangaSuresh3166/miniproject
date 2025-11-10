# app/utils.py
import random
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.core.mail import send_mail

def generate_numeric_otp(length=6):
    # ensure leading zeros allowed
    return ''.join(str(random.randint(0,9)) for _ in range(length))

def create_otp_for_user(user, ttl_minutes=10):
    from .models import PasswordResetOTP
    otp_code = generate_numeric_otp(6)
    expires_at = timezone.now() + timedelta(minutes=ttl_minutes)
    pr = PasswordResetOTP.objects.create(user=user, otp=otp_code, expires_at=expires_at)
    return pr

def send_otp_email(user, otp_obj):
    subject = "Your password reset OTP"
    message = (
        f"Hello {user.get_full_name() or user.username},\n\n"
        f"Your OTP for password reset is: {otp_obj.otp}\n"
        f"This code expires at {otp_obj.expires_at.strftime('%Y-%m-%d %H:%M:%S')} (server time).\n\n"
        "If you didn't request this, ignore this email.\n"
    )
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user.email]
    send_mail(subject, message, from_email, recipient_list, fail_silently=False)
