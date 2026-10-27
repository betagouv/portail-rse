from functools import wraps

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.urls import reverse_lazy

from entreprises.exceptions import EntrepriseNonQualifieeError
from entreprises.models import Entreprise
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
            return redirect(
                "entreprises:qualification", id_public=e.entreprise.id_public
            )

    return wrap


def entreprise_requise(function):
    @wraps(function)
    def wrap(request, id_public=None, **kwargs):
        if not id_public:
            # Import local pour éviter import circulaire
            from entreprises.views import get_current_entreprise

            entreprise = get_current_entreprise(request)
            if not entreprise:
                msg = "Commencez par ajouter une entreprise à votre compte utilisateur avant d'accéder à votre tableau de bord."
                if request.session.get("oidc_id_token"):
                    msg += "<br>Dans le cadre d'une connexion via ProConnect, vous pouvez vous déconnecter et vous reconnecter en précisant une autre entreprise de rattachement."
                messages.warning(request, msg)
                return redirect("entreprises:entreprises")
            return redirect(
                f"{request.resolver_match.app_name}:{request.resolver_match.url_name}",
                id_public=entreprise.id_public,
                **kwargs,
            )

        entreprise = get_object_or_404(Entreprise, id_public=id_public)
        if not Habilitation.existe(entreprise, request.user):
            raise PermissionDenied

        request.session["entreprise"] = entreprise.id

        return function(request, entreprise, **kwargs)

    return wrap


def entreprise_qualifiee_requise(function):
    @entreprise_requise
    @wraps(function)
    def wrap(request, entreprise, **kwargs):
        if caracteristiques := entreprise.dernieres_caracteristiques_qualifiantes:
            if caracteristiques != entreprise.caracteristiques_actuelles():
                messages.warning(
                    request,
                    f"Les informations affichées sont basées sur l'exercice comptable {caracteristiques.annee}. <a href='{reverse_lazy('entreprises:qualification', args=[entreprise.id_public])}'>Mettre à jour le profil de l'entreprise.</a>",
                )
            return function(request, entreprise, **kwargs)

        else:
            messages.warning(
                request,
                "Votre profil entreprise est incomplet ou doit être mis à jour suite à l'évolution d'une réglementation. Complétez-le pour avoir accès à toutes les fonctionnalités de votre tableau de bord.",
            )
            return redirect("entreprises:qualification", id_public=entreprise.id_public)

    return wrap
