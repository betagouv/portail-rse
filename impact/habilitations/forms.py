from django import forms

from utils.forms import DsfrForm


class InvitationForm(DsfrForm):
    email = forms.EmailField(
        label="Adresse e-mail", widget=forms.TextInput(attrs={"autofocus": True})
    )
