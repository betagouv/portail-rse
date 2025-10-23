from django.urls import path

from .views import ajout_document
from .views import analyses
from .views import etat
from .views import lancement_analyse
from .views import resultat
from .views import statut_analyse_ia
from .views import suppression

app_name = "analyseia"

urlpatterns = [
    path("analyses/", analyses, name="analyses"),
    path("ajout_document/", ajout_document, name="ajout_document"),
    path(
        "suppression/<int:id_analyse>/",
        suppression,
        name="suppression",
    ),
    path(
        "etat/<int:id_analyse>/",
        etat,
        name="etat",
    ),
    path(
        "lancement_analyse/<int:id_analyse>/",
        lancement_analyse,
        name="lancement_analyse",
    ),
    path(
        "resultat/<int:id_analyse>/",
        resultat,
        name="resultat",
    ),
    path(
        "fragments/statut/<int:id_analyse>/",
        statut_analyse_ia,
        name="statut_analyse",
    ),
]
