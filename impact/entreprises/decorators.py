from functools import wraps

from django.shortcuts import redirect

from entreprises.exceptions import EntrepriseNonQualifieeError


def entreprise_qualifiee_required(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        try:
            return function(request, *args, **kwargs)
        except EntrepriseNonQualifieeError as e:
            return redirect("entreprises:qualification", siren=e.entreprise.siren)

    return wrap
