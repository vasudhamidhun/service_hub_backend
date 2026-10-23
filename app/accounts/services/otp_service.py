
import secrets
import time
from django.core.mail import send_mail


_otp_store = {}

OTP_EXPIRY_SECONDS = 300  #5 mnts


def generate_otp(user_id, phone, profile_data):
    otp = f"{secrets.randbelow(1_000_000):06d}"

    _otp_store[user_id] = {
        "phone": phone,
        "otp": otp,
        "profile_data": profile_data,
        "expires_at": time.time() + OTP_EXPIRY_SECONDS,
    }

    return otp


def verify_otp(user_id, submitted_otp):
    stored = _otp_store.get(user_id)

    if not stored:
        return False

    if time.time() > stored["expires_at"]:
        _otp_store.pop(user_id, None)
        return False

    if not secrets.compare_digest(stored["otp"], submitted_otp):
        return False

    return True


def get_pending_profile(user_id):
    return _otp_store.get(user_id)


def clear_pending_profile(user_id):
    _otp_store.pop(user_id, None)



def send_otp_email(email, otp):
    send_mail(
        subject="Service Hub - Email Verification",
        message=(
            f"Your Service Hub verification OTP is {otp}.\n\n"
            "This OTP is valid for 5 minutes.\n"
            "Do not share this code with anyone."
        ),
        from_email=None,
        recipient_list=[email],
        fail_silently=False,
    )