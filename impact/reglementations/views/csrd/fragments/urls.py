from django.urls import path

from .enjeux import creation_enjeu
from .enjeux import deselection_enjeu
from .enjeux import liste_enjeux_selectionnes
from .enjeux import rafraichissement_esg
from .enjeux import selection_enjeux
from .enjeux import suppression_enjeu
from .enjeux_materiels import liste_enjeux_materiels
from .enjeux_materiels import selection_enjeux_materiels
from .rapport import selection_rapport
from .rapport import soumettre_lien_rapport
from reglementations.views.csrd.fragments.enjeux_materiels import (
    rafraichissement_enjeux_materiels,
)

urlpatterns = [
    path(
        "csrd/fragments/selection_enjeux/<int:csrd_id>/<str:esrs>",
        selection_enjeux,
        name="selection_enjeux",
    ),
    path(
        "csrd/fragments/creation_enjeu/<int:csrd_id>/<str:esrs>",
        creation_enjeu,
        name="creation_enjeu",
    ),
    path(
        "csrd/fragments/suppression_enjeu/<str:enjeu_id>",
        suppression_enjeu,
        name="suppression_enjeu",
    ),
    path(
        "csrd/fragments/deselection_enjeu/<int:enjeu_id>",
        deselection_enjeu,
        name="deselection_enjeu",
    ),
    path(
        "csrd/fragments/liste_enjeux_selectionnes/<int:csrd_id>/<int:selection>",
        liste_enjeux_selectionnes,
        name="liste_enjeux_selectionnes",
    ),
    path(
        "csrd/fragments/rafraichissement_esg/<int:csrd_id>",
        rafraichissement_esg,
        name="rafraichissement_esg",
    ),
    # sélection enjeux matériels :
    path(
        "csrd/fragments/rafraichissement_enjeux_materiels/<int:csrd_id>",
        rafraichissement_enjeux_materiels,
        name="rafraichissement_enjeux_materiels",
    ),
    path(
        "csrd/fragments/selection_enjeux_materiels/<int:csrd_id>/<str:esrs>",
        selection_enjeux_materiels,
        name="selection_enjeux_materiels",
    ),
    path(
        "csrd/fragments/liste_enjeux_materiels/<int:csrd_id>",
        liste_enjeux_materiels,
        name="liste_enjeux_materiels",
    ),
    path(
        "csrd/fragments/rapport/selection_rapport/<int:csrd_id>",
        selection_rapport,
        name="selection_rapport",
    ),
    path(
        "csrd/fragments/rapport/soumettre_lien_rapport/<int:csrd_id>",
        soumettre_lien_rapport,
        name="soumettre_lien_rapport",
    ),
]
