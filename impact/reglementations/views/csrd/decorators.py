from functools import wraps

from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from reglementations.models.csrd import DocumentAnalyseIA
from reglementations.models.csrd import Enjeu
from reglementations.models.csrd import RapportCSRD


def csrd_required(function):
    @wraps(function)
    def wrap(request, csrd_id, *args, **kwargs):
        csrd = get_object_or_404(RapportCSRD, id=csrd_id)

        if not csrd.modifiable_par(request.user):
            raise PermissionDenied(
                "L'utilisateur n'a pas les permissions nécessaires pour accéder à ce rapport CSRD"
            )
        return function(request, csrd_id, *args, **kwargs)

    return wrap


def enjeu_required(function):
    @wraps(function)
    def wrap(request, enjeu_id, *args, **kwargs):
        enjeu = get_object_or_404(Enjeu, pk=enjeu_id)

        if not enjeu.rapport_csrd.modifiable_par(request.user):
            raise PermissionDenied(
                "L'utilisateur n'a pas les permissions nécessaires pour accéder à ce rapport CSRD"
            )
        return function(request, enjeu_id, *args, **kwargs)

    return wrap


def document_required(function):
    @wraps(function)
    def wrap(request, id_document, *args, **kwargs):
        document = get_object_or_404(DocumentAnalyseIA, id=id_document)

        if not document.rapport_csrd.modifiable_par(request.user):
            raise PermissionDenied(
                "L'utilisateur n'a pas les permissions nécessaires pour accéder à ce fichier"
            )
        return function(request, id_document, *args, **kwargs)

    return wrap
