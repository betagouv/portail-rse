import django.utils.http
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (
    PasswordResetConfirmView as BasePasswordResetConfirmView,
)
from django.contrib.auth.views import PasswordResetView as BasePasswordResetView
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse

from .forms import AjoutEntrepriseConseillerForm
from .forms import ChoixTypeUtilisateurForm
from .forms import ProconnectUserEditionForm
from .forms import UserCreationForm
from .forms import UserEditionForm
from .forms import UserInvitationForm
from .forms import UserPasswordForm
from .models import User
from api.exceptions import APIError
from entreprises.models import Entreprise
from habilitations.enums import UserRole
from habilitations.models import Habilitation
from habilitations.models import HabilitationError
from invitations.models import Invitation
from logs import event_logger as logger
from reglementations.views import calculer_metriques_entreprise
from users.forms import message_erreur_proprietaires
from utils.tokens import check_token
from utils.tokens import make_token
from utils.tokens import uidb64


def creation(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            try:
                siren = form.cleaned_data["siren"]
                if entreprises := Entreprise.objects.filter(siren=siren):
                    entreprise = entreprises[0]
                    if habilitations := Habilitation.objects.filter(
                        entreprise=entreprise
                    ):
                        proprietaires_presents = [
                            habilitation.user for habilitation in habilitations
                        ]
                        messages.error(
                            request,
                            message_erreur_proprietaires(proprietaires_presents),
                        )
                        return render(request, "users/creation.html", {"form": form})

                else:
                    entreprise = Entreprise.search_and_create_entreprise(siren)
                user = form.save()
                Habilitation.ajouter(
                    entreprise,
                    user,
                    fonctions=form.cleaned_data["fonctions"],
                )
                if _send_confirm_email(request, user):
                    success_message = f"Votre compte a bien été créé. Un e-mail de confirmation a été envoyé à {user.email}. Confirmez votre adresse e-mail en cliquant sur le lien reçu avant de vous connecter."
                    messages.success(request, success_message)
                else:
                    error_message = f"L'e-mail de confirmation n'a pas pu être envoyé à {user.email}. Contactez-nous si cette adresse est légitime."
                    messages.error(request, error_message)
                return redirect("reglementations:tableau_de_bord", siren)
            except APIError as exception:
                messages.error(request, exception)
    else:
        simulation_data = request.session.get("simulation")
        form = UserCreationForm(initial=simulation_data)
    return render(request, "users/creation.html", {"form": form})


def _send_confirm_email(request, user):
    email = EmailMessage(
        to=[user.email],
        from_email=settings.DEFAULT_FROM_EMAIL,
    )
    email.template_id = settings.BREVO_CONFIRMATION_EMAIL_TEMPLATE
    path = reverse(
        "users:confirm_email",
        kwargs={"uidb64": uidb64(user), "token": make_token(user, "confirm_email")},
    )
    email.merge_global_data = {
        "confirm_email_url": request.build_absolute_uri(path),
    }
    return email.send()


def confirm_email(request, uidb64, token):
    # basé sur PasswordResetConfirmView.get_user()
    try:
        uid = django.utils.http.urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (
        TypeError,
        ValueError,
        OverflowError,
        User.DoesNotExist,
        ValidationError,
    ):
        user = None
    if user and check_token(user, "confirm_email", token):
        user.is_email_confirmed = True
        user.save()
        success_message = "Votre adresse e-mail a bien été confirmée. Vous pouvez à présent vous connecter."
        messages.success(request, success_message)
        return redirect("users:login")
    fail_message = "Le lien de confirmation est invalide."
    messages.error(request, fail_message)
    return redirect(reverse("erreur_terminale"))


def invitation(request, id_invitation, code):
    """L'invité arrive sur cette page grâce au lien contenu dans l'e-mail qu'il a reçu."""
    try:
        invitation = Invitation.objects.get(id=id_invitation)
    except Invitation.DoesNotExist:
        messages.error(request, "Cette invitation n'existe pas.")
        return redirect(reverse("erreur_terminale"))
    if invitation.est_expiree:
        messages.error(
            request,
            "L'invitation est expirée. Vous devez demander une nouvelle invitation à un des propriétaires de l'entreprise sur Portail RSE.",
        )
        return redirect(reverse("erreur_terminale"))
    if not check_token(invitation, "invitation", code):
        messages.error(request, "Cette invitation est incorrecte.")
        return redirect(reverse("erreur_terminale"))

    if request.method == "POST":
        form = UserInvitationForm(request.POST, invitation=invitation)
        email = form.data.get("email")
        if invitation.email != email:
            form.add_error("email", "L'e-mail ne correspond pas à l'invitation.")
        if form.is_valid():
            user = form.save()
            user.is_email_confirmed = True
            user.save()
            invitation.accepter(user, fonctions=form.cleaned_data["fonctions"])
            messages.success(
                request,
                "Votre compte a bien été créé. Connectez-vous pour collaborer avec les autres membres de l'entreprise.",
            )
            return redirect(
                "reglementations:tableau_de_bord", invitation.entreprise.siren
            )
        else:
            messages.error(
                request, "La création a échoué car le formulaire contient des erreurs."
            )
    else:
        form = UserInvitationForm(invitation=invitation)
    return render(
        request,
        "users/creation.html",
        {
            "form": form,
            "invitation": invitation,
            "code": code,
        },
    )


def invitation_proprietaire_tiers(request, id_invitation, code):
    """Landing page pour invitation propriétaire par conseiller RSE.

    Valide l'invitation puis redirige vers ProConnect.
    L'invitation est stockée en session pour être récupérée après authentification.
    """
    try:
        invitation = Invitation.objects.get(id=id_invitation)
    except Invitation.DoesNotExist:
        messages.error(request, "Cette invitation n'existe pas.")
        return redirect(reverse("erreur_terminale"))

    if invitation.est_expiree:
        messages.error(
            request,
            "L'invitation est expirée. Veuillez contacter le conseiller RSE qui a créé cette invitation.",
        )
        return redirect(reverse("erreur_terminale"))

    if not check_token(invitation, "invitation_proprietaire_tiers", code):
        messages.error(request, "Ce lien d'invitation est invalide.")
        return redirect(reverse("erreur_terminale"))

    if invitation.date_acceptation:
        messages.warning(request, "Cette invitation a déjà été acceptée.")
        return redirect("reglementations:tableau_de_bord", invitation.entreprise.siren)

    # Si utilisateur déjà connecté
    if request.user.is_authenticated:
        if invitation.email != request.user.email:
            messages.error(
                request, "Cette invitation ne correspond pas à votre adresse e-mail."
            )
            return redirect(reverse("erreur_terminale"))
        # Rediriger vers acceptation directe
        return redirect("users:accepter_role_proprietaire", id_invitation, code)

    # Stocker contexte en session et rediriger vers ProConnect
    request.session["pending_invitation_proprietaire"] = {
        "id": invitation.id,
        "code": code,
        "email": invitation.email,
        "entreprise_siren": invitation.entreprise.siren,
    }
    request.session["oidc_login_next"] = reverse(
        "users:finaliser_invitation_proprietaire"
    )
    request.session.save()

    return redirect("oidc_authentication_init")


@login_required()
def finaliser_invitation_proprietaire(request):
    """Finalise l'invitation propriétaire après authentification ProConnect."""
    pending = request.session.pop("pending_invitation_proprietaire", None)
    if not pending:
        messages.error(request, "Aucune invitation en attente.")
        return redirect("reglementations:tableau_de_bord")

    # Vérifier que l'email ProConnect correspond à l'invitation
    if request.user.email != pending["email"]:
        messages.error(
            request,
            f"L'adresse e-mail de votre compte ProConnect ({request.user.email}) "
            f"ne correspond pas à l'invitation ({pending['email']}).",
        )
        return redirect(reverse("erreur_terminale"))

    # Rediriger vers page d'acceptation existante
    return redirect(
        "users:accepter_role_proprietaire",
        pending["id"],
        pending["code"],
    )


def deconnexion(request):
    """Déconnexion par méthode GET

    La déconnexion django5 utilise uniquement la méthode POST.
    Cependant, sa réutilisation sur le site vitrine pose des problèmes d'autorisation
    (CORS et CSRF).
    https://docs.djangoproject.com/en/5.1/topics/auth/default/#django.contrib.auth.logout
    """
    if request.session.get("oidc_id_token"):
        # connecté via ProConnect, utilise le flow OIDC
        logger.info(
            "oidc:logout",
            {
                "session": request.session.session_key,
                "sub": str(request.user.oidc_sub_id),
            },
        )
        return redirect("oidc_logout_custom")

    # Sinon, déconnexion classique
    logout(request)
    return redirect(settings.SITES_FACILES_BASE_URL)


@login_required()
def account(request):
    if request.user.created_with_oidc:
        account_form = ProconnectUserEditionForm(instance=request.user)
    else:
        account_form = UserEditionForm(instance=request.user)
    password_form = UserPasswordForm(instance=request.user)
    if request.POST:
        if request.POST["action"] == "update-password":
            password_form = UserPasswordForm(request.POST, instance=request.user)
            if password_form.is_valid():
                password_form.save()
                success_message = (
                    "Votre mot de passe a bien été modifié. Veuillez vous reconnecter."
                )
                messages.success(request, success_message)
                return redirect("users:account")
            else:
                error_message = (
                    "La modification a échoué car le formulaire contient des erreurs."
                )
                messages.error(request, error_message)
        else:
            if request.user.created_with_oidc:
                account_form = ProconnectUserEditionForm(
                    request.POST, instance=request.user
                )
            else:
                account_form = UserEditionForm(request.POST, instance=request.user)
            if account_form.is_valid():
                account_form.save()
                if "email" in account_form.changed_data:
                    success_message = f"Votre adresse e-mail a bien été modifiée. Un e-mail de confirmation a été envoyé à {account_form.cleaned_data['email']}. Confirmez votre adresse e-mail en cliquant sur le lien reçu avant de vous reconnecter."
                    request.user.is_email_confirmed = False
                    request.user.save()
                    _send_confirm_email(request, request.user)
                    logout(request)
                else:
                    success_message = "Votre compte a bien été modifié."
                messages.success(request, success_message)
                return redirect("users:account")
            else:
                error_message = (
                    "La modification a échoué car le formulaire contient des erreurs."
                )
                messages.error(request, error_message)
    return render(
        request,
        "users/account.html",
        {"account_form": account_form, "password_form": password_form},
    )


class PasswordResetView(BasePasswordResetView):
    def form_valid(self, form):
        response = super(PasswordResetView, self).form_valid(form)
        success_message = "Un lien de ré-initialisation de votre mot de passe vous a été envoyé par e-mail. Vous devriez le recevoir d'ici quelques minutes."
        messages.success(self.request, success_message)
        return response


class PasswordResetConfirmView(BasePasswordResetConfirmView):
    def form_valid(self, form):
        response = super(PasswordResetConfirmView, self).form_valid(form)
        success_message = "Votre mot de passe a été réinitialisé avec succès. Vous pouvez à présent vous connecter."
        messages.success(self.request, success_message)
        return response

    def form_invalid(self, form):
        response = super(PasswordResetConfirmView, self).form_invalid(form)
        error_message = (
            "La réinitialisation a échoué car le formulaire contient des erreurs."
        )
        messages.error(self.request, error_message)
        return response


@login_required()
def post_login_dispatch(request):
    """Vue de dispatch après connexion (classique ou OIDC).

    Redirige l'utilisateur vers la bonne page selon son profil :
    - Si doit choisir son type → page de choix
    - Si conseiller RSE sans entreprise → tableau de bord conseiller
    - Sinon → tableau de bord entreprise (comportement par défaut)
    """
    # Si l'utilisateur doit choisir son type et ne l'a pas encore fait
    if request.user.doit_choisir_type_utilisateur and not request.session.get(
        "type_utilisateur_choisi"
    ):
        return redirect("users:choix_type_utilisateur")

    # Si c'est un conseiller RSE, rediriger vers son tableau de bord
    if request.user.is_conseiller_rse:
        return redirect("users:tableau_de_bord_conseiller")

    # Comportement par défaut : tableau de bord entreprise
    return redirect("reglementations:tableau_de_bord")


@login_required()
def choix_type_utilisateur(request):
    """Vue pour choisir entre conseiller RSE et membre d'entreprise.

    Cette vue est affichée aux nouveaux utilisateurs connectés via ProConnect
    qui n'ont pas encore d'habilitation sur une entreprise.
    """
    # Vérifier que l'utilisateur doit faire ce choix
    if not request.user.doit_choisir_type_utilisateur:
        return redirect("users:post_login_dispatch")

    if request.method == "POST":
        form = ChoixTypeUtilisateurForm(request.POST)
        if form.is_valid():
            type_choisi = form.cleaned_data["type_utilisateur"]

            if type_choisi == ChoixTypeUtilisateurForm.TYPE_CONSEILLER_RSE:
                request.user.is_conseiller_rse = True
                request.user.fonction_rse = form.cleaned_data["fonction_rse"]
                request.user.save()
                messages.success(
                    request,
                    "Vous êtes maintenant identifié comme conseiller RSE.",
                )
                return redirect("users:tableau_de_bord_conseiller")
            else:
                # Membre d'entreprise : marquer le choix fait et rediriger vers le dispatch
                request.session["type_utilisateur_choisi"] = True
                return redirect("users:post_login_dispatch")
    else:
        form = ChoixTypeUtilisateurForm()

    return render(request, "users/choix_type_utilisateur.html", {"form": form})


@login_required()
def tableau_de_bord_conseiller(request):
    """Tableau de bord pour les conseillers RSE.

    Gère l'ajout d'entreprise avec logique unifiée :
    - Entreprise existante avec propriétaire : refus attachement
    - Entreprise existante sans propriétaire : rattachement + invitation propriétaire
    - Entreprise inexistante : création + rattachement + invitation propriétaire
    """
    # Vérifier que l'utilisateur est bien un conseiller RSE
    if not request.user.is_conseiller_rse:
        messages.error(
            request,
            "Vous devez être identifié comme conseiller RSE pour accéder à cette page.",
        )
        return redirect("entreprises:entreprises")

    # Récupérer les entreprises en gestion (avec habilitation EDITEUR)
    habilitations = Habilitation.objects.filter(user=request.user).select_related(
        "entreprise"
    )

    # Enrichir chaque habilitation avec les metriques
    habilitations_enrichies = []
    for habilitation in habilitations:
        metriques = calculer_metriques_entreprise(habilitation.entreprise)
        habilitations_enrichies.append(
            {
                "habilitation": habilitation,
                "entreprise": habilitation.entreprise,
                "nombre_reglementations": metriques[
                    "nombre_reglementations_applicables"
                ],
                "pourcentage_vsme": metriques["pourcentage_vsme"],
            }
        )

    if request.method == "POST":
        form = AjoutEntrepriseConseillerForm(request.POST)
        if form.is_valid():
            try:
                siren = form.cleaned_data["siren"]
                email_proprietaire = form.cleaned_data.get("email_futur_proprietaire")

                # CAS 1 : Entreprise existe
                if Entreprise.objects.filter(siren=siren).exists():
                    entreprise = Entreprise.objects.get(siren=siren)

                    # Vérifier si le conseiller n'est pas déjà rattaché
                    if Habilitation.existe(entreprise, request.user):
                        messages.warning(
                            request,
                            f"Vous êtes déjà rattaché à l'entreprise {entreprise.denomination}.",
                        )
                        return redirect("users:tableau_de_bord_conseiller")

                    # CAS 1a : A un propriétaire → pas de rattachement
                    if entreprise.proprietaires:
                        messages.error(
                            request,
                            f"Vous n'avez pas été rattaché à l'entreprise {entreprise.denomination} car un compte y est déjà attachée. Demandez à votre client de vous inviter sur l'entreprise.",
                        )
                        return redirect("users:tableau_de_bord_conseiller")

                    # CAS 1b : Pas de propriétaire → rattachement + invitation
                    else:
                        Habilitation.ajouter(
                            entreprise,
                            request.user,
                            UserRole.PROPRIETAIRE,
                            fonctions=form.cleaned_data.get("fonctions"),
                            is_conseiller_rse=True,
                        )
                        _creer_invitation_proprietaire(
                            request, entreprise, email_proprietaire
                        )
                        messages.success(
                            request,
                            f"Vous avez été rattaché à l'entreprise {entreprise.denomination}. "
                            f"Une invitation a été envoyée à {email_proprietaire} pour devenir propriétaire.",
                        )
                        return redirect("users:tableau_de_bord_conseiller")

                # CAS 2 : Entreprise n'existe pas → création + rattachement + invitation
                else:
                    entreprise = Entreprise.search_and_create_entreprise(siren)
                    Habilitation.ajouter(
                        entreprise,
                        request.user,
                        UserRole.PROPRIETAIRE,
                        fonctions=form.cleaned_data.get("fonctions"),
                        is_conseiller_rse=True,
                    )
                    _creer_invitation_proprietaire(
                        request, entreprise, email_proprietaire
                    )
                    messages.success(
                        request,
                        f"L'entreprise {entreprise.denomination} a été créée. "
                        f"Une invitation a été envoyée à {email_proprietaire} pour devenir propriétaire.",
                    )
                    return redirect("users:tableau_de_bord_conseiller")

            except APIError as exception:
                messages.error(request, str(exception))
            except HabilitationError as exception:
                messages.error(request, str(exception))
        else:
            messages.error(request, "Le formulaire est incomplet.")
    else:
        form = AjoutEntrepriseConseillerForm()

    return render(
        request,
        "users/tableau_de_bord_conseiller.html",
        {"habilitations_enrichies": habilitations_enrichies, "form": form},
    )


def _creer_invitation_proprietaire(request, entreprise, email_proprietaire):
    """Crée une invitation propriétaire et envoie l'email."""
    invitation = Invitation.objects.create(
        entreprise=entreprise,
        email=email_proprietaire,
        role=UserRole.PROPRIETAIRE,
        inviteur=request.user,
    )
    _envoie_email_invitation_proprietaire_tiers(request, invitation)
    return invitation


@login_required()
def preremplissage_formulaire_compte(request):
    account_form = UserEditionForm(request.POST, instance=request.user)
    return render(
        request,
        "users/fragments/account_form.html",
        {"account_form": account_form},
    )


def _envoie_email_invitation_proprietaire_tiers(request, invitation):
    """Envoie un email d'invitation au futur propriétaire.

    Utilise le template dédié (BREVO_INVITATION_PROPRIETAIRE_TIERS_TEMPLATE)
    avec les mêmes variables pour une cohérence des emails.
    """
    email = EmailMessage(
        to=[invitation.email],
        from_email=settings.DEFAULT_FROM_EMAIL,
    )

    email.template_id = settings.BREVO_INVITATION_PROPRIETAIRE_TIERS_TEMPLATE

    # Vérifier si l'utilisateur existe déjà
    utilisateur_existe = User.objects.filter(email=invitation.email).exists()

    if utilisateur_existe:
        # Email pour utilisateur existant → page d'acceptation du rôle
        code = make_token(invitation, "invitation_proprietaire")
        path = reverse(
            "users:accepter_role_proprietaire",
            args=[invitation.id, code],
        )
    else:
        # Nouvel utilisateur → landing ProConnect
        code = make_token(invitation, "invitation_proprietaire_tiers")
        path = reverse(
            "users:invitation_proprietaire_tiers", args=[invitation.id, code]
        )

    inviteur_nom = f"{invitation.inviteur.prenom} {invitation.inviteur.nom}".strip()
    email.merge_global_data = {
        "denomination_entreprise": invitation.entreprise.denomination,
        "invitation_url": request.build_absolute_uri(path),
        "inviteur": inviteur_nom or "Un conseiller RSE",
        "role": UserRole(invitation.role).label,
    }
    return email.send()


@login_required()
def accepter_role_proprietaire(request, id_invitation, code):
    """Permet à un utilisateur existant d'accepter le rôle de propriétaire."""
    try:
        invitation = Invitation.objects.get(id=id_invitation)
    except Invitation.DoesNotExist:
        messages.error(request, "Cette invitation n'existe pas.")
        return redirect(reverse("erreur_terminale"))

    if invitation.est_expiree:
        messages.error(
            request,
            "L'invitation est expirée. Veuillez contacter le conseiller RSE qui a créé cette invitation.",
        )
        return redirect(reverse("erreur_terminale"))

    # Accepter les deux types de tokens (existant et nouveau via ProConnect)
    token_valide = check_token(
        invitation, "invitation_proprietaire", code
    ) or check_token(invitation, "invitation_proprietaire_tiers", code)
    if not token_valide:
        messages.error(request, "Ce lien d'invitation est invalide.")
        return redirect(reverse("erreur_terminale"))

    if invitation.email != request.user.email:
        messages.error(
            request,
            "Cette invitation ne correspond pas à votre adresse e-mail.",
        )
        return redirect(reverse("erreur_terminale"))

    if invitation.date_acceptation:
        messages.warning(
            request,
            "Cette invitation a déjà été acceptée.",
        )
        return redirect("reglementations:tableau_de_bord", invitation.entreprise.siren)

    try:
        invitation.accepter(request.user)
        messages.success(
            request,
            f"Vous êtes maintenant ajouté à l'entreprise {invitation.entreprise.denomination}.",
        )
        return redirect("reglementations:tableau_de_bord", invitation.entreprise.siren)
    except HabilitationError as exception:
        messages.error(request, "Une erreur lors de l'acceptation est survenue.")
    except Exception as exception:
        messages.error(request, "Une erreur est survenue.")
    return redirect(reverse("erreur_terminale"))
