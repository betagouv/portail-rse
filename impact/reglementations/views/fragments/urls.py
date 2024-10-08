from django.urls import path

from .enjeux import creation_enjeu
from .enjeux import rafraichissement_esg
from .enjeux import selection_enjeux
from .enjeux import suppression_enjeu

urlpatterns = [
    path(
        "csrd/fragments/selection_enjeux/<str:csrd_id>/<str:esrs>",
        selection_enjeux,
        name="selection_enjeux",
    ),
    path(
        "csrd/fragments/creation_enjeu/<str:csrd_id>/<str:esrs>",
        creation_enjeu,
        name="creation_enjeu",
    ),
    path(
        "csrd/fragments/suppression_enjeu/<str:enjeu_id>",
        suppression_enjeu,
        name="suppression_enjeu",
    ),
    path(
        "csrd/fragments/rafraichissement_esg/<str:csrd_id>",
        rafraichissement_esg,
        name="rafraichissement_esg",
    ),
]
