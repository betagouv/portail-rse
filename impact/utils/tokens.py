"""
La génération de token est une version simplifiée de django.contrib.auth.tokens.PasswordResetTokenGenerator.
"""
from django.utils.crypto import constant_time_compare
from django.utils.crypto import salted_hmac

import impact.settings


def get_token(user):
    hash_string = salted_hmac(
        "key_salt",
        f"{user.pk}{user.email}",
        secret=impact.settings.SECRET_KEY,
        algorithm="sha256",
    ).hexdigest()[::2]
    return hash_string


def check_token(user, token):
    return constant_time_compare(get_token(user), token)
