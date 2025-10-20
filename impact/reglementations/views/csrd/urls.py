from django.urls import path
from django.urls.conf import include

from reglementations.views.csrd.analyse_ia import ajout_document
from reglementations.views.csrd.analyse_ia import etat_analyse_IA
from reglementations.views.csrd.analyse_ia import lancement_analyse_IA
from reglementations.views.csrd.analyse_ia import resultat_IA_xlsx
from reglementations.views.csrd.analyse_ia import suppression_document
from reglementations.views.csrd.analyse_ia import synthese_resultat_IA_par_ESRS_xlsx
from reglementations.views.csrd.analyse_ia import synthese_resultat_IA_xlsx
from reglementations.views.csrd.csrd import datapoints_xlsx
from reglementations.views.csrd.csrd import enjeux_materiels_xlsx
from reglementations.views.csrd.csrd import enjeux_xlsx
from reglementations.views.csrd.csrd import gestion_csrd

urlpatterns = [
    path(
        "csrd/etape-<str:id_etape>",
        gestion_csrd,
        name="gestion_csrd",
    ),
    path(
        "csrd/<str:siren>/etape-<str:id_etape>",
        gestion_csrd,
        name="gestion_csrd",
    ),
    path("csrd/<str:siren>/enjeux.xlsx", enjeux_xlsx, name="enjeux_xlsx"),
    path(
        "csrd/<str:siren>/enjeux_materiels.xlsx",
        enjeux_materiels_xlsx,
        name="enjeux_materiels_xlsx",
    ),
    path(
        "csrd/<str:siren>/datapoints.xlsx",
        datapoints_xlsx,
        name="datapoints_xlsx",
    ),
    path(
        "csrd/<int:csrd_id>/ajout_document",
        ajout_document,
        name="ajout_document",
    ),
    path(
        "csrd/<int:id_document>/suppression",
        suppression_document,
        name="suppression_document",
    ),
    path(
        "ESRS-predict/<int:id_document>/<int:csrd_id>",
        etat_analyse_IA,
        name="etat_analyse_IA",
    ),
    path(
        "ESRS-predict/<int:id_document>/<int:csrd_id>/start",
        lancement_analyse_IA,
        name="lancement_analyse_IA",
    ),
    path(
        "ESRS-predict/<int:id_document>/resultats.xlsx",
        resultat_IA_xlsx,
        name="resultat_IA_xlsx",
    ),
    path(
        "ESRS-predict/<int:csrd_id>/synthese_resultats.xlsx",
        synthese_resultat_IA_xlsx,
        name="synthese_resultats_IA",
    ),
    path(
        "ESRS-predict/<int:csrd_id>/<str:code_esrs>",
        synthese_resultat_IA_par_ESRS_xlsx,
        name="synthese_resultats_IA_par_ESRS",
    ),
]

# Fragments HTMX
urlpatterns += [path("", include("reglementations.views.csrd.fragments.urls"))]
