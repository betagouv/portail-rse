import os

from .base import *  # noqa

# hosts / django-hosts
ALLOWED_HOSTS = os.getenv(
    "ALLOWED_HOSTS",
    "0.0.0.0,127.0.0.1,localhost,admin",
).split(",")

if DEBUG_TOOLBAR := os.getenv("DEBUG_TOOLBAR", False):
    INSTALLED_APPS.append("debug_toolbar")  # noqa: F405
    INTERNAL_IPS = ["127.0.0.1"]
    MIDDLEWARE.append("debug_toolbar.middleware.DebugToolbarMiddleware")  # noqa: F405

# Matomo :
MATOMO_DISABLED = True

# CSP :
# pour désactiver les CSP en mode dev, changer la var-env CSP_MODE=disabled

# Permet aux CSP ou au mode `report-only` de fonctionner correctement dans un environnement de dev
# en autorisant les connexions locales et à Svelte via websockets.
# Note : Sentry doit déjà être configuré à ce point pour un fonctionnement correct
if DEBUG:  # noqa: F405
    CSP_CONFIGURATION["DIRECTIVES"] = {  # noqa: F405
        k: v + ["ws:", "localhost:*"]
        for k, v in CSP_CONFIGURATION["DIRECTIVES"].items()  # noqa: F405
    }

# Django-extensions :
# pour `runserver_plus` : installer werkzeug
INSTALLED_APPS.append("django_extensions")  # noqa

# Gestion des e-mails :
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
