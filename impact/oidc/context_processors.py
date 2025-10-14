from django.conf import settings


def proconnect(request):
    return {
        "proconnect": bool(request.session.get("oidc_id_token")),
        "oidc_enabled": settings.OIDC_ENABLED,
    }
