from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("simulation", views.simulation, name="simulation"),
    path(
        "simulation/resultats", views.resultats_simulation, name="resultats_simulation"
    ),
    path("contact", views.contact, name="contact"),
    path("reglementations", views.reglementations, name="reglementations"),
    path("stats", views.stats, name="stats"),
    path("liens-menu", views.fragment_liens_menu, name="fragment_liens_menu"),
]
