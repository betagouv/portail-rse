from django.urls import path

from .views import actualisation_etat
from .views import ajout_document
from .views import analyses
from .views import lancement_analyse
from .views import resultat_v1
from .views import resultat_v2
from .views import statut_analyse_ia
from .views import suppression
from .views import synthese_resultat_v1
from .views import synthese_resultat_v1_par_ESRS

app_name = "analyseia"

urlpatterns = [
    path("analyses/", analyses, name="analyses"),
    path("analyses/<str:siren>/", analyses, name="analyses"),
    path("analyses/<str:siren>/ajout_document/", ajout_document, name="ajout_document"),
    path(
        "analyses/<str:siren>/ajout_document/<int:csrd_id>",
        ajout_document,
        name="ajout_document",
    ),
    path(
        "analyses/<int:id_analyse>/suppression/",
        suppression,
        name="suppression",
    ),
    path(
        "analyses/<int:id_analyse>/lancement_analyse/v<int:version_ia>",
        lancement_analyse,
        name="lancement_analyse",
    ),
    path(
        "analyses/<int:id_analyse>/etat/v<int:version_ia>",
        actualisation_etat,
        name="actualisation_etat",
    ),  # callback API IA
    path(
        "analyses/<int:id_analyse>/resultat/<str:rendu>",
        resultat_v1,
        name="resultat_v1",
    ),
    path(
        "analyses/<str:siren>/synthese/",
        synthese_resultat_v1,
        name="synthese_resultat_v1",
    ),
    path(
        "analyses/<str:siren>/synthese/<int:csrd_id>",
        synthese_resultat_v1,
        name="synthese_resultat_v1",
    ),
    path(
        "analyses/<str:siren>/<str:code_esrs>/<int:csrd_id>",
        synthese_resultat_v1_par_ESRS,
        name="synthese_resultat_v1_par_ESRS",
    ),
    path(
        "analyses/<str:siren>/<str:code_esrs>",
        synthese_resultat_v1_par_ESRS,
        name="synthese_resultat_v1_par_ESRS",
    ),
    path(
        "analyses/v2/<int:id_analyse>/resultat",
        resultat_v2,
        name="resultat_v2",
    ),
    path(
        "fragments/statut/<int:id_analyse>/",
        statut_analyse_ia,
        name="statut_analyse",
    ),
]
