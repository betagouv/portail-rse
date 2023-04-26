from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import PasswordResetForm as BasePasswordResetForm
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.forms import SetPasswordForm as BaseSetPasswordForm
from django.core.exceptions import ValidationError

from .models import User
from entreprises.forms import SirenField
from entreprises.models import Entreprise
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
    fonctions = forms.CharField(label="Fonction(s) dans la société")
    acceptation_cgu = forms.BooleanField(
        label=f"J’ai lu et j’accepte les CGU (Conditions Générales d'utilisation)",
        required=True,
    )

    class Meta:
        model = User
        fields = ("email", "acceptation_cgu", "reception_actualites", "prenom", "nom")
        labels = {
            "reception_actualites": "Je souhaite recevoir les actualités du projet Impact (optionnel)",
        }


class UserEditionForm(DsfrForm, forms.ModelForm):
    class Meta:
        model = User
        fields = ("prenom", "nom", "email", "reception_actualites")
        labels = {
            "reception_actualites": "Je souhaite recevoir les actualités du projet Impact (optionnel)",
        }


class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = ("email", "password", "is_active", "is_staff")


class PasswordResetForm(DsfrForm, BasePasswordResetForm):
    pass


class SetPasswordForm(DsfrForm, BaseSetPasswordForm):
    pass
