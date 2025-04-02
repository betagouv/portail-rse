import os

from .base import *  # noqa


# django-hosts : séparation de l'URL d'admin
# https://django-hosts.readthedocs.io/en/latest/
ROOT_HOSTCONF = "impact.hosts"
DEFAULT_HOST = "site"

# CNAME du site d'administation
ADMIN_CNAME = os.getenv("ADMIN_CNAME", "admin")

INSTALLED_APPS.append("django_hosts")  # noqa: F405

# Certaines extensions / applications ont des contraintes bien précises
# concerannt l'ordre de traitement des middlewares.
# Il est plus simple de retranscrire tous les middlewares plutôt que d'insérer
# les bons éléments aux bons endroits dans la chaîne de traitement.
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django_hosts.middleware.HostsRequestMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # ajout d'informations à l'utilisateur juste après l'identification
    "utils.middlewares.ExtendUserMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_hosts.middleware.HostsResponseMiddleware",
    # middlewares touchant à l'utilisation d'HTMX
    "utils.middlewares.HTMXRequestMiddleware",
    "utils.middlewares.HTMXRetargetMiddleware",
]

# Email
BREVO_API_KEY = os.getenv("BREVO_API_KEY")
EMAIL_BACKEND = "anymail.backends.brevo.EmailBackend"
ANYMAIL = {"BREVO_API_KEY": BREVO_API_KEY}
DEFAULT_FROM_EMAIL = "ne-pas-repondre@portail-rse.beta.gouv.fr"
CONTACT_EMAIL = os.getenv("CONTACT_EMAIL")
BREVO_CONFIRMATION_EMAIL_TEMPLATE = 1
BREVO_RESULTAT_ANALYSE_IA_TEMPLATE = 65

# Sentry
SENTRY_DSN = os.getenv("SENTRY_DSN")
SENTRY_ENV = os.getenv("SENTRY_ENV", "production")

if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production.
        traces_sample_rate=0.1,
        # If you wish to associate users to errors (assuming you are using
        # django.contrib.auth) you may enable sending PII data.
        send_default_pii=True,
        environment=SENTRY_ENV,
    )

# Report URI : Sentry will log CSP violations to this URI if set
if SENTRY_SECURITY_HEADER_ENDPOINT := os.getenv("SENTRY_SECURITY_HEADER_ENDPOINT", ""):
    # `report-uri` directive is deprecated in favor of `report-to`
    # however django-csp CSP internal building is using it.
    # According to Sentry documentation, the report URI must pass a `sentry_environment`
    # request parameter for sorting-out CSP reports.
    # See : https://sentry.incubateur.net/organizations/betagouv/issues/118719/?project=75&query=is%3Aunresolved&referrer=issue-stream&statsPeriod=24h&stream_index=0
    CSP_CONFIGURATION["DIRECTIVES"]["report-uri"] = [  # noqa: F405
        SENTRY_SECURITY_HEADER_ENDPOINT + f"&sentry_environment={SENTRY_ENV}"
    ]
    # 'report-to' is a reference to a key of the map defined in the `Report-to` HTTP header
    # for future compatibility, but is currently *inactive* for most browsers by now (09.2024).
    # Uncomment when widely supported.
    # (see Sentry setup for value)
    # CSP_CONFIGURATION["DIRECTIVES"]["report-to"] = "csp-endpoint"
