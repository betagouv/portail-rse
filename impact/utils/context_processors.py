from django.conf import settings


def custom_settings(request):
    # allows direct access to some relevant settings
    return {"matomo_enabled": not settings.MATOMO_DISABLED}
