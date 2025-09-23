from functools import wraps

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.urls import reverse_lazy

from entreprises.exceptions import EntrepriseNonQualifieeError
from entreprises.models import Entreprise
from entreprises.views import get_current_entreprise
from habilitations.models import Habilitation


def entreprise_qualifiee_required(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        try:
            return function(request, *args, **kwargs)
        except EntrepriseNonQualifieeError as e:
            messages.warning(
                request,
                e.message,
            )
            return redirect("entreprises:qualification", siren=e.entreprise.siren)

    return wrap


def entreprise_qualifiee_requise(function):
    @wraps(function)
    def wrap(request, siren=None, **kwargs):
        if not siren:
            entreprise = get_current_entreprise(request)
            if not entreprise:
                messages.warning(
                    request,
                    "Commencez par ajouter une entreprise à votre compte utilisateur avant d'accéder à votre tableau de bord",
                )
                return redirect("entreprises:entreprises")
            return redirect(
                f"{request.resolver_match.app_name}:{request.resolver_match.url_name}",
                siren=entreprise.siren,
                **kwargs,
            )

        entreprise = get_object_or_404(Entreprise, siren=siren)
        if not Habilitation.existe(entreprise, request.user):
            raise PermissionDenied

        request.session["entreprise"] = entreprise.siren

        if caracteristiques := entreprise.dernieres_caracteristiques_qualifiantes:
            if caracteristiques != entreprise.caracteristiques_actuelles():
                messages.warning(
                    request,
                    f"Les informations affichées sont basées sur l'exercice comptable {caracteristiques.annee}. <a href='{reverse_lazy('entreprises:qualification', args=[entreprise.siren])}'>Mettre à jour le profil de l'entreprise.</a>",
                )
            return function(request, entreprise, **kwargs)

        else:
            messages.warning(
                request,
                "Veuillez renseigner le profil de l'entreprise pour accéder au tableau de bord.",
            )
            return redirect("entreprises:qualification", siren=entreprise.siren)

    return wrap
