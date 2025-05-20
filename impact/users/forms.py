from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import PasswordResetForm as BasePasswordResetForm
from django.contrib.auth.forms import SetPasswordForm as BaseSetPasswordForm
from django.core.exceptions import ValidationError

from .models import User
from entreprises.forms import SirenField
from entreprises.models import Entreprise
from habilitations.models import FONCTIONS_MAX_LENGTH
from habilitations.models import FONCTIONS_MIN_LENGTH
from habilitations.models import Habilitation
from invitations.models import Invitation
from utils.forms import DsfrForm


class LoginForm(DsfrForm, AuthenticationForm):
    username = forms.EmailField(
        label="Adresse e-mail", widget=forms.TextInput(attrs={"autofocus": True})
    )

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        self.fields["password"].label = "Mot de passe"

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.is_email_confirmed:
            raise ValidationError(
                "Merci de confirmer votre adresse e-mail en cliquant sur le lien reçu avant de vous connecter.",
            )


class UserPasswordForm(DsfrForm, forms.ModelForm):
    password1 = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text=password_validation.password_validators_help_text_html(),
    )
    password2 = forms.CharField(
        label="Confirmation du mot de passe",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    class Meta:
        model = User
        fields = ()

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if (password1 or password2) and password1 != password2:
            raise forms.ValidationError("Les mots de passe sont différents")
        return password2

    def _post_clean(self):
        super()._post_clean()
        # Validate the password after self.instance is updated with form data
        # by super().
        password = self.cleaned_data.get("password2")
        if password:
            try:
                password_validation.validate_password(password, self.instance)
            except forms.ValidationError as error:
                self.add_error("password1", error)

    def save(self, commit=True):
        user = super().save(commit=False)
        if password := self.cleaned_data.get("password1"):
            # Save the provided password in hashed format
            user.set_password(password)
        if commit:
            user.save()
        return user


class UserCreationForm(UserPasswordForm):
    siren = SirenField()
    fonctions = forms.CharField(
        label="Fonction(s) dans la société",
        min_length=FONCTIONS_MIN_LENGTH,
        max_length=FONCTIONS_MAX_LENGTH,
    )
    acceptation_cgu = forms.BooleanField(
        label="J’ai lu et j’accepte les CGU (Conditions Générales d'utilisation)",
        required=True,
    )
    proprietaires_presents = []

    class Meta:
        model = User
        fields = ("email", "acceptation_cgu", "reception_actualites", "prenom", "nom")
        labels = {
            "reception_actualites": "Je souhaite recevoir les actualités du Portail RSE (optionnel)",
        }

    def clean_siren(self):
        siren = self.cleaned_data.get("siren")
        if entreprises := Entreprise.objects.filter(siren=siren):
            entreprise = entreprises[0]
            if habilitations := Habilitation.objects.filter(entreprise=entreprise):
                self.proprietaires_presents = [
                    habilitation.user for habilitation in habilitations
                ]
                raise forms.ValidationError(
                    "Cette entreprise a déjà au moins un propriétaire."
                )
        return siren

    def message_erreur_proprietaires(self):
        if len(self.proprietaires_presents) == 1:
            email_cache = cache_partiellement_un_email(
                self.proprietaires_presents[0].email
            )
            message = f"Il existe déjà un propriétaire sur cette entreprise. Contactez la personne concernée ({email_cache}) ou notre support (contact@portail-rse.beta.gouv.fr)."
        else:
            emails_caches = ", ".join(
                [
                    cache_partiellement_un_email(proprietaire.email)
                    for proprietaire in self.proprietaires_presents
                ]
            )
            message = f"Il existe déjà des propriétaires sur cette entreprise. Contactez une des personnes concernées ({emails_caches}) ou notre support (contact@portail-rse.beta.gouv.fr)."
        return message


def cache_partiellement_un_email(email):
    nom, domaine = email.split("@")
    etoiles = "*" * (len(nom) - 2)
    return f"{nom[0]}{etoiles}{nom[-1]}@{domaine}"


class InvitationForm(UserCreationForm):
    code = forms.CharField(widget=forms.HiddenInput())
    id_invitation = forms.IntegerField(widget=forms.HiddenInput())

    def clean_siren(self):
        siren = self.cleaned_data.get("siren")
        if Entreprise.objects.filter(siren=siren).count() != 1:
            raise forms.ValidationError(
                "Cette entreprise n'existe plus dans Portail-RSE."
            )
        return siren

    def _post_clean(self):
        super()._post_clean()
        code = self.cleaned_data.get("code")
        id_invitation = self.cleaned_data.get("id_invitation")
        if invitations := Invitation.objects.filter(id=id_invitation, code=code):
            invitation = invitations[0]
            if invitation.est_expiree:
                self.add_error("id_invitation", "Cette invitation est expirée.")
        else:
            self.add_error("code", "Cette invitation n'existe plus dans Portail-RSE.")


class UserEditionForm(DsfrForm, forms.ModelForm):
    class Meta:
        model = User
        fields = ("prenom", "nom", "email", "reception_actualites")
        labels = {
            "reception_actualites": "Je souhaite recevoir les actualités du Portail RSE (optionnel)",
        }


class PasswordResetForm(DsfrForm, BasePasswordResetForm):
    pass


class SetPasswordForm(DsfrForm, BaseSetPasswordForm):
    pass
