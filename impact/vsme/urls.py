from django.urls import path

import vsme.views as views

app_name = "vsme"
urlpatterns = [
    path(
        "vsme/<str:etape>/",
        views.etape_vsme,
        name="etape_vsme",
    ),
    path(
        "vsme/<str:siren>/<str:etape>/",
        views.etape_vsme,
        name="etape_vsme",
    ),
    path(
        "indicateurs/vsme/",
        views.indicateurs_vsme,
        name="indicateurs_vsme",
    ),
    path(
        "indicateurs/vsme/<str:siren>/",
        views.indicateurs_vsme,
        name="indicateurs_vsme",
    ),
    path(
        "indicateurs/vsme/<str:siren>/<int:annee>/",
        views.indicateurs_vsme,
        name="indicateurs_vsme",
    ),
    path(
        "indicateurs/vsme/<int:vsme_id>/categorie/<str:categorie>/",
        views.categorie_vsme,
        name="categorie_vsme",
    ),
    path(
        "indicateurs/vsme/<int:vsme_id>/exigence-de-publication/<str:exigence_de_publication_code>/",
        views.exigence_de_publication_vsme,
        name="exigence_de_publication_vsme",
    ),
    path(
        "indicateurs/vsme/<int:vsme_id>/indicateur/<str:indicateur_schema_id>/",
        views.indicateur_vsme,
        name="indicateur_vsme",
    ),
    path(
        "indicateurs/vsme/<int:vsme_id>/indicateur/<str:indicateur_schema_id>/pertinent/",
        views.toggle_pertinent,
        name="toggle_pertinent",
    ),
]
