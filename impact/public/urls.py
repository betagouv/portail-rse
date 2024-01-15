from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("simulation", views.simulation, name="simulation"),
    path("mentions-legales", views.mentions_legales, name="mentions_legales"),
    path(
        "politique-confidentialite",
        views.politique_confidentialite,
        name="politique_confidentialite",
    ),
    path("cgu", views.cgu, name="cgu"),
    path("contact", views.contact, name="contact"),
    path("reglementations", views.reglementations, name="reglementations"),
    path("stats", views.stats, name="stats"),
]
