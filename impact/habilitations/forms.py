from django import forms

from habilitations.enums import UserRole
from utils.forms import DsfrForm


class InvitationForm(DsfrForm):
    email = forms.EmailField(
        label="Adresse e-mail", widget=forms.TextInput(attrs={"autofocus": True})
    )
    role = forms.ChoiceField(
        label="Rôle du futur membre",
        choices=UserRole.choices,
        widget=forms.Select(attrs={"class": "form-control"}),
        error_messages={
            "required": "Veuillez sélectionner un rôle pour le futur membre."
        },
    )
