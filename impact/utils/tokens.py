"""
La génération de token est une version simplifiée de django.contrib.auth.tokens.PasswordResetTokenGenerator.
"""
from django.conf import settings
from django.utils.crypto import constant_time_compare
from django.utils.crypto import salted_hmac
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


def make_token(user, key_salt):
    hash_string = salted_hmac(
        key_salt,
        f"{user.pk}{user.email}",
        secret=settings.SECRET_KEY,
        algorithm="sha256",
    ).hexdigest()[::2]
    return hash_string


def check_token(user, key_salt, token):
    return constant_time_compare(make_token(user, key_salt), token)


def uidb64(user):
    return urlsafe_base64_encode(force_bytes(user.pk))
