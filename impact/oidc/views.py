import logging

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import SuspiciousOperation
from django.http.response import HttpResponseBadRequest
from django.http.response import HttpResponseServerError
from django.shortcuts import redirect
from django.shortcuts import resolve_url
from lasuite.oidc_login.views import OIDCAuthenticationCallbackView as CallbackView

import api.infos_entreprise as api_entreprise
from api.exceptions import APIError
from entreprises.models import Entreprise
from habilitations.models import Habilitation
from utils.anonymisation import cache_partiellement_un_email

logger = logging.getLogger(__name__)


class OIDCAuthenticationCallbackView(CallbackView):
    """
    En cas de connexion via ProConnect, le routage "normal" est détourné
    et traité par des vues spécifiques pour certains cas d'utilisation :
        - nouvel utilisateur pour entreprise existante
        - nouvel utilisateur pour nouvelle entreprise
        - utilisateur existant pour entreprise inconnue
        - utilisateur existant pour entreprise existante
    => plutôt que de rediriger vers `LOGIN_REDIRECT_URL` ou `next_url`,
       on redirige vers `oidc.views.dispatch_view()`
    """

    @property
    def success_url(self):
        next_url = self.request.session.get("oidc_login_next", None)
        return next_url or resolve_url("/oidc/dispatch")


def dispatch_view(request):
    """
    En cas de succès d'une connexion ProConnect, cette vue 'récupère' le routage
    pour pouvoir aiguiller ou traiter les cas spécifiques.
    """
    if not request.session.get("oidc_user_claims"):
        raise SuspiciousOperation(
            "Impossible de trouver les `claims` utilisateur, dont le SIREN de connexion"
        )

    oidc_siren = request.session["oidc_user_claims"]["siren"]
    entreprise = None
    url_destination = resolve_url(settings.LOGIN_REDIRECT_URL)

    logger.info(f"Dispatching for SIREN: {oidc_siren}")

    # Vérification de l'existence de l'entreprise choisie via ProConnect
    try:
        entreprise = Entreprise.objects.get(siren=oidc_siren)
    except Entreprise.DoesNotExist:
        logger.warning(
            f"L'entreprise sélectionnée sur ProConnect ({oidc_siren}) n'existe pas encore sur le portail"
        )

    # l'entreprise n'existe pas encore en base
    if not entreprise:
        try:
            entreprise = _creation_entreprise(oidc_siren, request.user)
        except APIError as ex:
            logger.error(f"Impossible de contacter l'API entreprise : {ex}")
            return HttpResponseBadRequest(
                f"Impossible de contacter l'API entreprise : {ex}"
            )
        except Exception as ex:
            logger.error(
                f"Erreur lors de la creation de l'entreprise SIREN:{oidc_siren} : {ex}"
            )
            return HttpResponseServerError(
                f"Erreur lors de la creation de l'entreprise SIREN:{oidc_siren} : {ex}"
            )
        else:
            # on sélectione l'entreprise nouvellement créée pour le tableau de bord
            request.session["entreprise"] = oidc_siren
            request.session.save()
            messages.success(
                request,
                f"L'entreprise {entreprise} a bien été créé et vous en êtes le premier membre propriétaire.",
            )
            return redirect(url_destination)

    # l'entreprise existe déjà en base :
    # l'utilisateur connecté en fait-il partie ?
    if Habilitation.existe(entreprise, request.user):
        # on peut directement rediriger vers le tableau de bord
        request.session["entreprise"] = oidc_siren
        request.session.save()
        messages.success(
            request,
            f"Vous avez choisi de vous connecter via ProConnect avec : {entreprise}.",
        )
        return redirect(url_destination)

    # cas limite :
    # une entreprise est existante, mais sans utilisateur rattaché
    # par ex. suite à une suppression de l'utilisateur via l'admin
    # => l'utilisateur devient propriétaire
    if Habilitation.objects.filter(entreprise=entreprise).count() == 0:
        Habilitation.ajouter(entreprise, request.user)
        return redirect(url_destination)

    # l'entreprise et l'utilisateur existent mais l'utilisateur n'en est pas membre
    messages.warning(request, _message_erreur_proprietaire(entreprise))
    return redirect("entreprises:entreprises")


# Fonctions utilitaires


def _creation_entreprise(siren, user):
    # création d'une nouvelle entreprise et association de l'utilisateur
    # identifié comme premier proprietaire
    infos_entreprise = api_entreprise.infos_entreprise(siren)
    entreprise = Entreprise.objects.create(
        siren=infos_entreprise["siren"],
        denomination=infos_entreprise["denomination"],
        categorie_juridique_sirene=infos_entreprise["categorie_juridique_sirene"],
        code_pays_etranger_sirene=infos_entreprise["code_pays_etranger_sirene"],
        code_NAF=infos_entreprise["code_NAF"],
    )
    Habilitation.ajouter(entreprise, user)
    return entreprise


def _message_erreur_proprietaire(entreprise):
    # petite duplication et petit changement de texte, mais pas de dépendance vers `users`
    proprietaires = Habilitation.objects.filter(
        entreprise=entreprise, role="proprietaire"
    ).select_related("user")

    if proprietaires.count() == 1:
        email_cache = cache_partiellement_un_email(proprietaires[0].user.email)
        message = f"Il existe déjà un propriétaire pour l'entreprise {entreprise}. Contactez la personne concernée ({email_cache}) ou notre support (contact@portail-rse.beta.gouv.fr)."
    elif proprietaires.count() > 1:
        emails_caches = ", ".join(
            [cache_partiellement_un_email(h.user.email) for h in proprietaires]
        )
        message = f"Il existe déjà des propriétaires pour l'entreprise {entreprise}. Contactez une des personnes concernées ({emails_caches}) ou notre support (contact@portail-rse.beta.gouv.fr)."
    return message
