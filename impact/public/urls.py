from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("simulation", views.simulation, name="simulation"),
    path(
        "simulation/fragments/preremplissage-formulaire-simulation",
        views.preremplissage_formulaire_simulation,
        name="preremplissage_formulaire_simulation",
    ),
    path(
        "simulation/resultats", views.resultats_simulation, name="resultats_simulation"
    ),
    path("contact", views.contact, name="contact"),
    path("stats", views.stats, name="stats"),
    path("liens-menu", views.fragment_liens_menu, name="fragment_liens_menu"),
    path("erreur", views.erreur_terminale, name="erreur_terminale"),
]
