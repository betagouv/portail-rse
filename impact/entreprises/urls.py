from django.urls import path

from . import views

app_name = "entreprises"
urlpatterns = [
    path("entreprises", views.index, name="entreprises"),
    path("entreprises/<str:siren>", views.qualification, name="qualification"),
    path("api/search-entreprise/<str:siren>", views.search_entreprise),
    path(
        "entreprises/fragments/recherche-entreprise",
        views.recherche_entreprise,
        name="recherche_entreprise",
    ),
    path(
        "entreprises/fragments/preremplissage-siren/<str:siren>",
        views.preremplissage_siren,
        name="preremplissage_siren",
    ),
]
