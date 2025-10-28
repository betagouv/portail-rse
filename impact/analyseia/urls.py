from django.urls import path

from .views import ajout_document
from .views import analyses
from .views import etat
from .views import lancement_analyse
from .views import resultat
from .views import statut_analyse_ia
from .views import suppression
from .views import synthese_resultat
from .views import synthese_resultat_par_ESRS

app_name = "analyseia"

urlpatterns = [
    path("analyses/", analyses, name="analyses"),
    path("analyses/<str:siren>/", analyses, name="analyses"),
    path("analyses/<str:siren>/ajout_document/", ajout_document, name="ajout_document"),
    path(
        "analyses/<int:id_analyse>/suppression/",
        suppression,
        name="suppression",
    ),
    path(
        "analyses/<int:id_analyse>/etat/",
        etat,
        name="etat",
    ),
    path(
        "analyses/lancement_analyse/<int:id_analyse>/",
        lancement_analyse,
        name="lancement_analyse",
    ),
    path(
        "analyses/<int:id_analyse>/resultat/<str:rendu>",
        resultat,
        name="resultat",
    ),
    path(
        "analyses/<str:siren>/synthese/",
        synthese_resultat,
        name="synthese_resultat",
    ),
    path(
        "analyses/<str:siren>/synthese/<int:csrd_id>",
        synthese_resultat,
        name="synthese_resultat",
    ),
    path(
        "analyses/<str:siren>/<str:code_esrs>/<int:csrd_id>",
        synthese_resultat_par_ESRS,
        name="synthese_resultat_par_ESRS",
    ),
    path(
        "analyses/<str:siren>/<str:code_esrs>",
        synthese_resultat_par_ESRS,
        name="synthese_resultat_par_ESRS",
    ),
    path(
        "fragments/statut/<int:id_analyse>/",
        statut_analyse_ia,
        name="statut_analyse",
    ),
]
