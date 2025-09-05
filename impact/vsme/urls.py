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
        "indicateurs/<str:siren>",
        views.indicateurs_vsme,
        name="indicateurs_vsme",
    ),
    path(
        "indicateurs/exigence-de-publication/<str:siren>",
        views.exigence_de_publication,
        name="exigence_de_publication",
    ),
    path(
        "indicateurs/<str:siren>/<str:categorie>",
        views.indicateurs_vsme_categorie,
        name="indicateurs_vsme_categorie",
    ),
    path(
        "indicateurs/vsme/<int:vsme_id>/<str:indicateur_schema_id>",
        views.indicateur_vsme,
        name="indicateur_vsme",
    ),
]
