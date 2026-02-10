from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import PasswordResetForm as BasePasswordResetForm
from django.contrib.auth.forms import SetPasswordForm as BaseSetPasswordForm
from django.core.exceptions import ValidationError

from .models import User
from entreprises.forms import PreremplissageSirenForm
from habilitations.models import FONCTIONS_MAX_LENGTH
from habilitations.models import FONCTIONS_MIN_LENGTH
from utils.anonymisation import cache_partiellement_un_email
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


class UserCreationForm(UserPasswordForm, PreremplissageSirenForm):
    fonctions = forms.CharField(
        label="Fonction(s) dans la société",
        min_length=FONCTIONS_MIN_LENGTH,
        max_length=FONCTIONS_MAX_LENGTH,
    )
    acceptation_cgu = forms.BooleanField(
        label="J’ai lu et j’accepte les CGU (Conditions Générales d'utilisation)",
        required=True,
    )

    class Meta:
        model = User
        fields = ("email", "acceptation_cgu", "reception_actualites", "prenom", "nom")
        labels = {
            "reception_actualites": "Je souhaite recevoir les actualités du Portail RSE (optionnel)",
        }


class UserInvitationForm(UserCreationForm):
    siren = None

    def __init__(self, *args, **kwargs):
        invitation = kwargs.pop("invitation", None)
        super().__init__(*args, **kwargs)
        if invitation:
            self.fields["fonctions"].label = (
                f"Fonction(s) dans la société {invitation.entreprise.denomination}"
            )
            self.fields["email"].initial = invitation.email


def message_erreur_proprietaires(proprietaires_presents):
    if len(proprietaires_presents) == 1:
        email_cache = cache_partiellement_un_email(proprietaires_presents[0].email)
        message = f"Il existe déjà un propriétaire sur cette entreprise. Contactez la personne concernée ({email_cache}) ou notre support (contact@portail-rse.beta.gouv.fr)."
    else:
        emails_caches = ", ".join(
            [
                cache_partiellement_un_email(proprietaire.email)
                for proprietaire in proprietaires_presents
            ]
        )
        message = f"Il existe déjà des propriétaires sur cette entreprise. Contactez une des personnes concernées ({emails_caches}) ou notre support (contact@portail-rse.beta.gouv.fr)."
    return message


class UserEditionForm(DsfrForm, forms.ModelForm):
    is_conseiller_rse = forms.BooleanField(
        required=False, label="Je suis conseiller RSE"
    )

    class Meta:
        model = User
        fields = ("prenom", "nom", "email", "is_conseiller_rse", "reception_actualites")
        labels = {
            "reception_actualites": "Je souhaite recevoir les actualités du Portail RSE (optionnel)",
        }


class PasswordResetForm(DsfrForm, BasePasswordResetForm):
    pass


class SetPasswordForm(DsfrForm, BaseSetPasswordForm):
    pass


class ChoixTypeUtilisateurForm(DsfrForm, forms.Form):
    TYPE_MEMBRE_ENTREPRISE = "membre_entreprise"
    TYPE_CONSEILLER_RSE = "conseiller_rse"

    TYPE_CHOICES = [
        (TYPE_MEMBRE_ENTREPRISE, "Je suis membre d'une entreprise"),
        (TYPE_CONSEILLER_RSE, "Je suis conseiller RSE"),
    ]

    type_utilisateur = forms.ChoiceField(
        label="Quel est votre profil ?",
        choices=TYPE_CHOICES,
        widget=forms.RadioSelect,
    )
    fonction_rse = forms.ChoiceField(
        label="Fonction(s) dans l'accompagnement",
        choices=User._meta.get_field("fonction_rse").choices,
        required=False,
    )


class AjoutEntrepriseConseillerForm(DsfrForm, PreremplissageSirenForm):
    """Formulaire unifié pour qu'un conseiller RSE ajoute une entreprise accompagnée.

    Gère tous les cas :
    - Entreprise existante avec propriétaire : pas de rattachement
    - Entreprise existante sans propriétaire : rattachement + invitation propriétaire
    - Entreprise inexistante : création + rattachement + invitation propriétaire
    """

    email_futur_proprietaire = forms.EmailField(
        label="Adresse e-mail du contact principal de l’entreprise accompagnée",
        required=True,
        help_text="Une invitation lui sera envoyée afin qu’elle puisse accéder au tableau de bord de son entreprise.",
    )
