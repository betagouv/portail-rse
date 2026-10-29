from django import forms

from utils.forms import DsfrForm
from utils.forms import SafeEmailField


class PartageForm(DsfrForm):
    email = SafeEmailField(
        label="Adresse e-mail", widget=forms.TextInput(attrs={"autofocus": True})
    )
