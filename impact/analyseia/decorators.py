from functools import wraps

from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from habilitations.models import Habilitation
from reglementations.models.csrd import RapportCSRD


def csrd_valide_si_presente(function):
    @wraps(function)
    def wrap(request, entreprise, *args, csrd_id=None, **kwargs):
        if not csrd_id:
            return function(request, entreprise, *args, csrd=None, **kwargs)

        csrd = get_object_or_404(RapportCSRD, id=csrd_id)

        if not Habilitation.existe(csrd.entreprise, request.user):
            raise PermissionDenied(
                "L'utilisateur n'a pas les permissions nécessaires pour accéder à ce rapport CSRD"
            )

        return function(request, entreprise, *args, csrd=csrd, **kwargs)

    return wrap
