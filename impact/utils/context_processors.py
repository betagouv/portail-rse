from django.conf import settings


def custom_settings(_):
    # allows direct access to some relevant settings
    ctx = {
        "cookie_domain": settings.COOKIE_DOMAIN,
        "matomo_enabled": not settings.MATOMO_DISABLED,
        "sites_faciles_base_url": settings.SITES_FACILES_BASE_URL,
    }

    if hasattr(settings, "sentry_dsn"):
        ctx |= {
            "sentry_dsn": settings.SENTRY_DSN,
            "sentry_env": settings.SENTRY_ENV,
        }

    return ctx
