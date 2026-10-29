from django import forms

from habilitations.enums import UserRole
from utils.forms import DsfrForm
from utils.forms import SafeEmailField


class InvitationForm(DsfrForm):
    email = SafeEmailField(
        label="Adresse e-mail",
        help_text="La personne recevra un e-mail d'invitation pour créer son compte et rejoindre l'entreprise. Si elle possède déjà un compte utilisateur sur le Portail RSE, elle sera directement ajoutée dans les utilisateurs de l'entreprise.",
        widget=forms.TextInput(attrs={"autofocus": False}),
    )
    role = forms.ChoiceField(
        label="Rôle du futur membre",
        choices=UserRole.choices,
        widget=forms.Select(attrs={"class": "form-control"}),
        error_messages={
            "required": "Veuillez sélectionner un rôle pour le futur membre."
        },
    )
