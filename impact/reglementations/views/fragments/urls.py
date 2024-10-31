from django.urls import path

from .enjeux import creation_enjeu
from .enjeux import liste_enjeux_selectionnes
from .enjeux import rafraichissement_esg
from .enjeux import selection_enjeux
from .enjeux import suppression_enjeu

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
        "csrd/fragments/liste_enjeux_selectionnes/<int:csrd_id>",
        liste_enjeux_selectionnes,
        name="liste_enjeux_selectionnes",
    ),
    path(
        "csrd/fragments/rafraichissement_esg/<int:csrd_id>",
        rafraichissement_esg,
        name="rafraichissement_esg",
    ),
]
