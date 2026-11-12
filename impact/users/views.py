import django.utils.http
from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (
    PasswordResetConfirmView as BasePasswordResetConfirmView,
)
from django.contrib.auth.views import PasswordResetView as BasePasswordResetView
from django.core.exceptions import BadRequest
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse

from .forms import ChoixTypeUtilisateurForm
from .forms import ProconnectUserEditionForm
from .forms import UserEditionForm
from .forms import UserPasswordForm
from .models import User
from invitations.models import Invitation
from logs import event_logger as logger
from utils.messages import message_error_sans_html
from utils.messages import message_success_sans_html
from utils.messages import message_warning_sans_html
from utils.tokens import check_token
from utils.tokens import make_token
from utils.tokens import uidb64


def creation(request):
    """Fin des créations de compte sur le service. Fait uniquement avec ProConnect

    Redirection pour éviter des 404 aux utilisateurs et pour le SEO
    """
    return redirect(reverse("users:login"))


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
        message_success_sans_html(request, success_message)
        return redirect("users:login")
    raise BadRequest("Le lien de confirmation est invalide.")


def invitation(request, id_invitation, code):
    """L'invité arrive sur cette page grâce au lien contenu dans l'e-mail qu'il a reçu.

    Valide l'invitation puis redirige vers ProConnect pour authentification.
    """
    try:
        invitation = Invitation.objects.get(id=id_invitation)
    except Invitation.DoesNotExist:
        raise BadRequest("Cette invitation n'existe pas.")

    if invitation.est_expiree:
        raise BadRequest(
            "L'invitation est expirée. Vous devez demander une nouvelle invitation à la personne qui a créé cette invitation."
        )

    if not check_token(invitation, "invitation", code):
        raise BadRequest("Cette invitation est incorrecte.")

    if invitation.date_acceptation:
        message_warning_sans_html(request, "Cette invitation a déjà été acceptée.")
        return redirect(
            "tableau_de_bord:tableau_de_bord", invitation.entreprise.id_public
        )

    # Si utilisateur déjà connecté
    if request.user.is_authenticated:
        if invitation.email != request.user.email:
            raise BadRequest(
                "Cette invitation ne correspond pas à votre adresse e-mail."
            )
        # Rediriger vers acceptation directe
        return redirect("users:accepter_invitation", id_invitation, code)

    # Rediriger vers ProConnect
    request.session["page_suivante"] = reverse(
        "users:accepter_invitation", args=[id_invitation, code]
    )
    request.session.save()

    return redirect("oidc_authentication_init")


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
            if request.user.email == settings.USER_TEST_EMAIL:
                message_error_sans_html(
                    request,
                    "Cette modification est interdite pour ce compte de test.",
                )
                return redirect("users:account")
            password_form = UserPasswordForm(request.POST, instance=request.user)
            if password_form.is_valid():
                password_form.save()
                success_message = (
                    "Votre mot de passe a bien été modifié. Veuillez vous reconnecter."
                )
                message_success_sans_html(request, success_message)
                return redirect("users:account")
            else:
                error_message = (
                    "La modification a échoué car le formulaire contient des erreurs."
                )
                message_error_sans_html(request, error_message)
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
                message_success_sans_html(request, success_message)
                return redirect("users:account")
            else:
                error_message = (
                    "La modification a échoué car le formulaire contient des erreurs."
                )
                message_error_sans_html(request, error_message)
    return render(
        request,
        "users/account.html",
        {"account_form": account_form, "password_form": password_form},
    )


class PasswordResetView(BasePasswordResetView):
    def form_valid(self, form):
        response = super().form_valid(form)
        success_message = "Un lien de ré-initialisation de votre mot de passe vous a été envoyé par e-mail. Vous devriez le recevoir d'ici quelques minutes."
        message_success_sans_html(self.request, success_message)
        return response


class PasswordResetConfirmView(BasePasswordResetConfirmView):
    def form_valid(self, form):
        response = super().form_valid(form)
        success_message = "Votre mot de passe a été réinitialisé avec succès. Vous pouvez à présent vous connecter."
        message_success_sans_html(self.request, success_message)
        return response

    def form_invalid(self, form):
        response = super().form_invalid(form)
        error_message = (
            "La réinitialisation a échoué car le formulaire contient des erreurs."
        )
        message_error_sans_html(self.request, error_message)
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
    if request.user.doit_choisir_type_utilisateur:
        return redirect("users:choix_type_utilisateur")

    # Si c'est un conseiller RSE, rediriger vers son tableau de bord
    if request.user.is_conseiller_rse:
        return redirect("tableau_de_bord:tableau_de_bord_conseiller")

    # Comportement par défaut : tableau de bord entreprise
    return redirect("tableau_de_bord:tableau_de_bord")


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
                message_success_sans_html(
                    request,
                    "Vous êtes maintenant identifié comme conseiller RSE.",
                )
                return redirect("tableau_de_bord:tableau_de_bord_conseiller")
            else:
                request.user.is_conseiller_rse = False
                request.user.save()
                return redirect("tableau_de_bord:tableau_de_bord")

    else:
        form = ChoixTypeUtilisateurForm()

    return render(request, "users/choix_type_utilisateur.html", {"form": form})


@login_required()
def preremplissage_formulaire_compte(request):
    account_form = UserEditionForm(request.POST, instance=request.user)
    return render(
        request,
        "users/fragments/account_form.html",
        {"account_form": account_form},
    )


@login_required()
def accepter_invitation(request, id_invitation, code):
    """Permet à un utilisateur existant d'accepter une invitation (quel que soit le rôle)."""
    try:
        invitation = Invitation.objects.get(id=id_invitation)
    except Invitation.DoesNotExist:
        raise BadRequest("Cette invitation n'existe pas.")

    if invitation.est_expiree:
        raise BadRequest(
            "L'invitation est expirée. Veuillez contacter le conseiller RSE qui a créé cette invitation."
        )

    if not check_token(invitation, "invitation", code):
        raise BadRequest("Ce lien d'invitation est invalide.")

    if invitation.email != request.user.email:
        raise BadRequest("Cette invitation ne correspond pas à votre adresse e-mail.")

    if invitation.date_acceptation:
        message_warning_sans_html(
            request,
            "Cette invitation a déjà été acceptée.",
        )
        return redirect(
            "tableau_de_bord:tableau_de_bord", invitation.entreprise.id_public
        )

    if request.user.is_conseiller_rse is None:
        # Le cas d'usage imaginé est que la personne invitée est un responsable de l'entreprise.
        # On préremplit pour simplifier la navigation future (pas de choix lors de la prochaine
        # connexion).
        request.user.is_conseiller_rse = False
        request.user.save()

    invitation.accepter(request.user)
    message_success_sans_html(
        request,
        f"Vous êtes maintenant ajouté à l'entreprise {invitation.entreprise.denomination}.",
    )
    return redirect("tableau_de_bord:tableau_de_bord", invitation.entreprise.id_public)
