from django.contrib import admin
from django.http import HttpResponseForbidden
from django.http import HttpResponseNotFound
from django.http import HttpResponseServerError
from django.urls import path

# URLs / chemins pour le site d'admin

urlpatterns = [
    path("", admin.site.urls),
]

print("patterns:", urlpatterns)

# La gestion des pages d'erreurs doit être redéfinie pour le nouveau site,
# sinon il tente d'utiliser les templates et vues par défaut (404.html ...)
# ce qui mène à des erreurs de lookup et des redirections sans fin
# (ce qui inonde Sentry).
# On surcharge donc les principales erreurs qui sont déjà définies.


def not_found(_, exception=None):
    return HttpResponseNotFound("Not found")


def forbidden(_, exception=None):
    return HttpResponseForbidden("Forbidden")


def server_error(_, exception=None):
    return HttpResponseServerError("Server error")


handler403 = forbidden
handler404 = not_found
handler500 = server_error
