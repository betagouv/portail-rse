from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("entreprise", views.entreprise, name="entreprise"),
    path("siren", views.siren, name="siren"),
    path("mentions-legales", views.mentions_legales, name="mentions_legales"),
    path(
        "donnees-personnelles", views.donnees_personnelles, name="donnees_personnelles"
    ),
    path("cgu", views.cgu, name="cgu"),
    path("contact", views.contact, name="contact"),
]
