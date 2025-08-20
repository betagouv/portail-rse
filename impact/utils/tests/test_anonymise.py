from django.conf import settings

from utils.anonymisation import cache_partiellement_un_email
from utils.anonymisation import cache_partiellement_un_mot


def test_email():
    assert cache_partiellement_un_email("alice@domain.test") == "a***e@domain.test"
    assert (
        cache_partiellement_un_email(settings.SUPPORT_EMAIL) == settings.SUPPORT_EMAIL
    )


def test_mot():
    assert cache_partiellement_un_mot("alice") == "a***e"
    assert cache_partiellement_un_mot("carole") == "c****e"
