from django import forms
from django.contrib.auth.forms import AuthenticationForm, ReadOnlyPasswordHashField
from django.contrib.auth.forms import PasswordResetForm as BasePasswordResetForm
from django.contrib.auth.forms import SetPasswordForm as BaseSetPasswordForm
from django.core.exceptions import ValidationError

from public.forms import DsfrForm
from entreprises.models import Entreprise
from .models import User


class LoginForm(DsfrForm, AuthenticationForm):
    username = forms.EmailField(
        label="Email", widget=forms.TextInput(attrs={"autofocus": True})
    )

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        self.fields["password"].label = "Mot de passe"


class UserCreationForm(DsfrForm, forms.ModelForm):
    password1 = forms.CharField(label="Mot de passe", widget=forms.PasswordInput)
    password2 = forms.CharField(
        label="Confirmation du mot de passe", widget=forms.PasswordInput
    )
    siren = forms.CharField(
        label="Votre numéro SIREN",
        help_text="Saisissez un numéro SIREN valide, disponible sur le Kbis de votre organisation",
        min_length=9,
        max_length=9,
    )
    acceptation_cgu = forms.BooleanField(
        label="J’ai lu et j’accepte la politique de confidentialité et les CGUs",
        required=True,
    )

    class Meta:
        model = User
        fields = ("email", "acceptation_cgu", "reception_actualites", "prenom", "nom")
        labels = {
            "reception_actualites": "Je souhaite recevoir les actualités du projet Impact",
        }

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Les mots de passe sont différents")
        return password2

    def clean_siren(self):
        cleaned_data = self.cleaned_data.get("siren")
        try:
            int(cleaned_data)
        except ValueError:
            raise ValidationError("Le siren est incorrect")
        return cleaned_data

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        entreprise, _ = Entreprise.objects.get_or_create(
            siren=self.cleaned_data.get("siren")
        )
        if commit:
            user.save()
            entreprise.users.add(user)
            entreprise.save()
        return user


class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = ("email", "password", "is_active", "is_staff")


class PasswordResetForm(DsfrForm, BasePasswordResetForm):
    pass


class SetPasswordForm(DsfrForm, BaseSetPasswordForm):
    new_password1 = forms.CharField(label="Mot de passe", widget=forms.PasswordInput)
    new_password2 = forms.CharField(
        label="Confirmation du mot de passe", widget=forms.PasswordInput
    )

    def __init__(self, *args, **kwargs):
        super(SetPasswordForm, self).__init__(*args, **kwargs)
