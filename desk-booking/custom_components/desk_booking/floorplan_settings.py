"""Floorplan settings and salted password verification; no plaintext persisted."""
import hashlib
import hmac
import secrets
from urllib.parse import urlsplit

DEFAULT_BOOKING_URL = 'https://places.cloud.microsoft/'


def booking_url(value):
    value = value.strip()
    parts = urlsplit(value)
    if len(value) > 2048 or any(ord(c) < 33 for c in value) or parts.scheme != 'https' or not parts.hostname or parts.username or parts.password:
        raise ValueError('Invalid reservation URL')
    return value


def hash_password(password):
    if not isinstance(password, str) or not 1 <= len(password) <= 256:
        raise ValueError('Invalid password')
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 600000).hex()
    return salt + ':' + digest


def verify_password(password, stored):
    if not isinstance(password, str) or not 1 <= len(password) <= 256:
        return False
    try:
        salt, digest = stored.split(':')
        actual = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 600000).hex()
        return hmac.compare_digest(actual, digest)
    except (ValueError, AttributeError):
        return False
