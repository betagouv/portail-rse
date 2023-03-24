from django import forms

from entreprises.forms import SirenField
from entreprises.models import Entreprise
from entreprises.models import RAISON_SOCIALE_MAX_LENGTH
from utils.forms import DsfrForm


class SirenForm(DsfrForm):
    siren = SirenField()


class EligibiliteForm(DsfrForm, forms.ModelForm):
    raison_sociale = forms.CharField()

    class Meta:
        model = Entreprise
        fields = ["effectif", "bdese_accord", "raison_sociale", "siren"]

    def clean_raison_sociale(self):
        raison_sociale = self.cleaned_data.get("raison_sociale")
        return raison_sociale[:RAISON_SOCIALE_MAX_LENGTH]


class ContactForm(DsfrForm):
    email = forms.EmailField(label="Votre email")
    subject = forms.CharField(
        label="Sujet",
        max_length=255,
    )
    message = forms.CharField(widget=forms.Textarea())
