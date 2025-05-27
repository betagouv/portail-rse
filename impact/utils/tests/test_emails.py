from django.conf import settings

from utils.emails import cache_partiellement_un_email


def test():
    assert cache_partiellement_un_email("alice@domain.test") == "a***e@domain.test"
    assert (
        cache_partiellement_un_email(settings.SUPPORT_EMAIL) == settings.SUPPORT_EMAIL
    )
