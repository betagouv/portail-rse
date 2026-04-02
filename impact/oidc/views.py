from django.conf import settings
from django.contrib import messages
from django.core.exceptions import SuspiciousOperation
from django.core.mail import EmailMessage
from django.http.response import HttpResponseBadRequest
from django.http.response import HttpResponseServerError
from django.shortcuts import redirect
from django.shortcuts import resolve_url
from django.urls import reverse
from lasuite.oidc_login.views import OIDCAuthenticationCallbackView as CallbackView

from api.exceptions import APIError
from entreprises.models import Entreprise
from habilitations.enums import UserRole
from habilitations.models import Habilitation
from logs import event_logger as logger
from utils.anonymisation import cache_partiellement_un_email


class OIDCAuthenticationCallbackView(CallbackView):
    """
    En cas de connexion via ProConnect, le routage "normal" est détourné
    et traité par des vues spécifiques pour certains cas d'utilisation :
        - nouvel utilisateur pour entreprise existante,
        - nouvel utilisateur pour nouvelle entreprise,
        - utilisateur existant pour entreprise inconnue,
        - utilisateur existant pour entreprise existante
    => plutôt que de rediriger vers `LOGIN_REDIRECT_URL` ou `next_url`,
       on redirige vers `oidc.views.proconnect_dispatch_view()` pour traitement.
    Note :
        Certaines portions de la vue de "dispatch" sont dupliquées ou remaniées.
        AMA il est préférable d'avoir les 2 types de connexion compartimentés.
        Une première tentative d'intégration dans le code existant a échouée :
            - code et flow illisible pour les 2 types d'identification,
            - on fini par ne plus discerner clairement les responsabilités de chaque flow.
        Il est à mon avis plus clair d'avoir tout en seul point pour chaque flow (PC ou e-mail/mdp),
        même avec un peu de code dupliqué.
        Libre à tout un chacun d'ameliorer ou simplifier au besoin...
    """

    @property
    def success_url(self):
        return reverse("proconnect_dispatch_view")


def proconnect_dispatch_view(request):
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

    logger.info(
        "oidc:login",
        {
            "sub": str(request.user.oidc_sub_id),
            "siren": oidc_siren,
            "session": request.session.session_key,
        },
    )

    # vérification de l'existence de l'entreprise choisie via ProConnect
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
                f"Impossible de contacter l'API entreprise, veuillez-vous déconnecter et rééssayer ultérieurement ({ex})"
            )
        except Exception as ex:
            msg = (
                f"Erreur lors de la creation de l'entreprise SIREN: {oidc_siren} : {ex}"
            )
            logger.error(msg)
            return HttpResponseServerError(msg)

    # l'entreprise existe en base.
    # l'utilisateur connecté en est-il membre ?
    if Habilitation.existe(entreprise, request.user):
        # on peut directement rediriger vers le tableau de bord
        request.session["entreprise"] = oidc_siren
        request.session.save()
        messages.success(
            request,
            f"Vous avez choisi de vous connecter via ProConnect avec : {entreprise}.",
        )
    elif Habilitation.objects.filter(entreprise=entreprise).count():
        # d'autres utilisateurs sont membres de l'entreprise
        Habilitation.ajouter(entreprise, request.user, role=UserRole.EDITEUR)
        _envoie_email_aux_proprietaires_actuels(request, entreprise)
    else:
        Habilitation.ajouter(entreprise, request.user, role=UserRole.PROPRIETAIRE)

    if request.session.get("page_suivante"):
        # cas d'une invitation faite par un conseiller
        url_destination = request.session.get("page_suivante")
        request.session["page_suivante"] = None
        request.session.save()
    else:
        url_destination = resolve_url(settings.LOGIN_REDIRECT_URL)
    return redirect(url_destination)


# Fonctions utilitaires


def _creation_entreprise(siren, user):
    # création d'une nouvelle entreprise et association de l'utilisateur
    # identifié comme premier proprietaire
    entreprise = Entreprise.search_and_create_entreprise(siren)
    Habilitation.ajouter(entreprise, user)
    return entreprise


def _envoie_email_aux_proprietaires_actuels(request, entreprise):
    destinataires = [utilisateur.email for utilisateur in entreprise.proprietaires]
    email = EmailMessage(
        to=destinataires,
        from_email=settings.DEFAULT_FROM_EMAIL,
    )
    email.template_id = settings.BREVO_ARRIVEE_NOUVEAU_MEMBRE_TEMPLATE
    path = request.build_absolute_uri(
        reverse(
            "reglementations:tableau_de_bord",
            kwargs={
                "siren": entreprise.siren,
            },
        )
    )
    email.merge_global_data = {
        "denomination_entreprise": entreprise.denomination,
        "email_nouveau_membre": request.user.email,
        "url_administration_entreprise": path,
    }
    email.send()


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
