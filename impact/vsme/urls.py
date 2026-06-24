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
        "vsme/<int:vsme_id>/export/xlsx",
        views.export_vsme_xlsx,
        name="export_vsme_xlsx",
    ),
    path(
        "vsme/<int:vsme_id>/export/pptx",
        views.export_vsme_pptx,
        name="export_vsme_pptx",
    ),
    path(
        "indicateurs/vsme/",
        views.categories_vsme,
        name="categories_vsme",
    ),
    path(
        "indicateurs/vsme/<str:siren>/",
        views.categories_vsme,
        name="categories_vsme",
    ),
    path(
        "indicateurs/vsme/<str:siren>/<int:annee>/",
        views.categories_vsme,
        name="categories_vsme",
    ),
    path(
        "indicateurs/vsme/<int:vsme_id>/categorie/<str:categorie_id>/",
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
        "indicateurs/vsme/<int:vsme_id>/indicateur/<str:indicateur_schema_id>/reinitialiser/",
        views.reinitialiser_indicateur_vsme,
        name="reinitialiser_indicateur_vsme",
    ),
]
