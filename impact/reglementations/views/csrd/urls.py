from django.urls import path
from django.urls.conf import include

from reglementations import views

urlpatterns = [
    path("csrd", views.csrd.guide_csrd, name="csrd"),
    path("csrd/guide/<str:siren>", views.csrd.guide_csrd, name="csrd"),
    path(
        "csrd/guide/<str:siren>/phase-<int:phase>",
        views.csrd.guide_csrd,
        name="csrd_phase",
    ),
    path(
        "csrd/guide/<str:siren>/phase-<int:phase>/etape-<int:etape>",
        views.csrd.guide_csrd,
        name="csrd_etape",
    ),
    path(
        "csrd/guide/<str:siren>/phase-<int:phase>/etape-<int:etape>-<int:sous_etape>",
        views.csrd.guide_csrd,
        name="csrd_sous_etape",
    ),
    path(
        "csrd/<str:siren>/etape-<str:id_etape>",
        views.csrd.gestion_csrd,
        name="gestion_csrd",
    ),
    path("csrd/<str:siren>/enjeux.xlsx", views.csrd.enjeux_xlsx, name="enjeux_xlsx"),
    path(
        "csrd/<str:siren>/enjeux_materiels.xlsx",
        views.csrd.enjeux_materiels_xlsx,
        name="enjeux_materiels_xlsx",
    ),
    path(
        "csrd/<str:siren>/datapoints.xlsx",
        views.csrd.datapoints_xlsx,
        name="datapoints_xlsx",
    ),
    path(
        "csrd/<int:csrd_id>/ajout_document",
        views.csrd.ajout_document,
        name="ajout_document",
    ),
    path(
        "csrd/<int:id_document>/suppression",
        views.csrd.suppression_document,
        name="suppression_document",
    ),
    path(
        "ESRS-predict/<int:id_document>",
        views.csrd.etat_analyse_IA,
        name="etat_analyse_IA",
    ),
    path(
        "ESRS-predict/<int:id_document>/start",
        views.csrd.lancement_analyse_IA,
        name="lancement_analyse_IA",
    ),
    path(
        "ESRS-predict/<int:id_document>/resultats.xlsx",
        views.csrd.resultat_IA_xlsx,
        name="resultat_IA_xlsx",
    ),
    path(
        "ESRS-predict/<int:csrd_id>/synthese_resultats.xlsx",
        views.csrd.synthese_resultat_IA_xlsx,
        name="synthese_resultats_IA",
    ),
]

# Fragments HTMX
urlpatterns += [path("", include("reglementations.views.csrd.fragments.urls"))]
