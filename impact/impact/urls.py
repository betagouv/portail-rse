"""Portail-RSE URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.urls import include
from django.urls import path

if settings.DEBUG_TOOLBAR:
    from debug_toolbar.toolbar import debug_toolbar_urls


def trigger_error(request):
    division_by_zero = 1 / 0  # noqa


urlpatterns = (
    [
        path("", include("public.urls")),
        path("", include("entreprises.urls")),
        path("", include("habilitations.urls")),
        path("", include("reglementations.urls")),
        path("", include("users.urls")),
        path("", include("vsme.urls")),
        path("trigger-error-for-sentry-debug/", trigger_error),
    ]
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
)

if settings.OIDC_ENABLED:
    urlpatterns += [
        path("oidc/", include("oidc.urls")),
    ]

if settings.DEBUG_TOOLBAR:
    urlpatterns.extend(debug_toolbar_urls())

# note : admin site path is in a distinct file for `django-hosts`
if settings.DEBUG:
    from django.contrib import admin

    urlpatterns.append(path("admin", admin.site.urls))
