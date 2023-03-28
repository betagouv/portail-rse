from django import forms

from entreprises.forms import SirenField
from entreprises.models import DENOMINATION_MAX_LENGTH
from entreprises.models import Entreprise
from utils.forms import DsfrForm


class SirenForm(DsfrForm):
    siren = SirenField()


class EligibiliteForm(DsfrForm, forms.ModelForm):
    denomination = forms.CharField()

    class Meta:
        model = Entreprise
        fields = ["effectif", "bdese_accord", "denomination", "siren"]

    def clean_denomination(self):
        denomination = self.cleaned_data.get("denomination")
        return denomination[:DENOMINATION_MAX_LENGTH]


class ContactForm(DsfrForm):
    email = forms.EmailField(label="Votre email")
    subject = forms.CharField(
        label="Sujet",
        max_length=255,
    )
    message = forms.CharField(widget=forms.Textarea())
