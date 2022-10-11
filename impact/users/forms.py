from django import forms
from django.contrib.auth.forms import AuthenticationForm, ReadOnlyPasswordHashField

from public.forms import DsfrForm
from public.models import Entreprise
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
        required=False,
        min_length=9,
        max_length=9,
    )

    class Meta:
        model = User
        fields = ("email",)

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Les mots de passe sont différents")
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if siren := self.cleaned_data.get("siren"):
            entreprise = Entreprise.objects.get(siren=siren)
        if commit:
            user.save()
            if siren:
                entreprise.users.add(user)
                entreprise.save()
        return user


class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = ("email", "password", "is_active", "is_staff")
