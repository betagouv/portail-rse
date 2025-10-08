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

from .forms import UserCreationForm
from .forms import UserEditionForm
from .forms import UserInvitationForm
from .forms import UserPasswordForm
from .models import User
from api.exceptions import APIError
from entreprises.models import Entreprise
from entreprises.views import search_and_create_entreprise
from habilitations.models import Habilitation
from invitations.models import Invitation
from logs import event_logger as logger
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
                    entreprise = search_and_create_entreprise(siren)
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
    try:
        invitation = Invitation.objects.get(id=id_invitation)
    except Invitation.DoesNotExist:
        messages.error(request, "Cette invitation n'existe pas.")
        return redirect(reverse("erreur_terminale"))
    if invitation.est_expiree:
        messages.error(
            request,
            "L'invitation est expirée. Vous devez demander une nouvelle invitation à un des propriétaires de l'entreprise sur Portail-RSE.",
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
