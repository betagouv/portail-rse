from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import AuthenticationForm, ReadOnlyPasswordHashField
from django.contrib.auth.forms import PasswordResetForm as BasePasswordResetForm
from django.contrib.auth.forms import SetPasswordForm as BaseSetPasswordForm

from utils.forms import DsfrForm
from entreprises.models import Entreprise
from entreprises.forms import SirenField
from habilitations.models import Habilitation
from .models import User


class LoginForm(DsfrForm, AuthenticationForm):
    username = forms.EmailField(
        label="Email", widget=forms.TextInput(attrs={"autofocus": True})
    )

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        self.fields["password"].label = "Mot de passe"


class UserPasswordForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput,
        help_text=password_validation.password_validators_help_text_html(),
    )
    password2 = forms.CharField(
        label="Confirmation du mot de passe",
        widget=forms.PasswordInput,
    )

    class Meta:
        model = User
        fields = ("email",)

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


class UserCreationForm(DsfrForm, UserPasswordForm):
    siren = SirenField(
        label="Numéro SIREN",
        help_text="Saisissez un numéro SIREN valide, disponible sur le Kbis de votre organisation ou sur l'Annuaire des Entreprises",
    )
    acceptation_cgu = forms.BooleanField(
        label="J’ai lu et j’accepte la politique de confidentialité et les CGUs",
        required=True,
    )
    fonctions = forms.CharField(label="Fonction(s) dans la société")

    class Meta:
        model = User
        fields = ("email", "acceptation_cgu", "reception_actualites", "prenom", "nom")
        labels = {
            "prenom": "Prénom",
            "reception_actualites": "Je souhaite recevoir les actualités du projet Impact (optionnel)",
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        # Save the provided password in hashed format
        user.set_password(self.cleaned_data["password1"])
        entreprise, _ = Entreprise.objects.get_or_create(
            siren=self.cleaned_data.get("siren")
        )
        if commit:
            user.save()
            Habilitation.objects.create(
                user=user,
                entreprise=entreprise,
                fonctions=self.cleaned_data["fonctions"],
            )
            entreprise.save()
        return user


class UserEditionForm(DsfrForm, UserPasswordForm):
    password1 = forms.CharField(
        label="Mot de passe (optionnel)",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text=password_validation.password_validators_help_text_html(),
        required=False,
    )
    password2 = forms.CharField(
        label="Confirmation du mot de passe (optionnel)",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        required=False,
    )

    class Meta:
        model = User
        fields = ("prenom", "nom", "email", "reception_actualites")
        labels = {
            "prenom": "Prénom",
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
