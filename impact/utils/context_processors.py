from django.conf import settings


def custom_settings(_):
    # allows direct access to some relevant settings
    return {
        "cookie_domain": settings.COOKIE_DOMAIN,
        "matomo_enabled": not settings.MATOMO_DISABLED,
        "sentry_dsn": settings.SENTRY_DSN,
        "sentry_env": settings.SENTRY_ENV,
        "sites_faciles_base_url": settings.SITES_FACILES_BASE_URL,
    }
