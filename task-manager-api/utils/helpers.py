import re
from datetime import datetime, timezone


def utc_now():
    """Substitui datetime.utcnow() (deprecated desde Python 3.12), mantendo datetime naive em UTC."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def format_date(date_obj):
    if date_obj:
        return str(date_obj)
    return None


def calculate_percentage(part, total):
    if total == 0:
        return 0
    return round((part / total) * 100, 2)


def validate_email(email):
    if not email:
        return False
    return bool(re.match(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$', email))
