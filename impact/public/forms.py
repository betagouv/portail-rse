from django import forms

from entreprises.forms import SirenField
from entreprises.models import Entreprise, RAISON_SOCIALE_MAX_LENGTH
from utils.forms import DsfrForm


class SirenForm(DsfrForm):
    siren = SirenField(
        label="Votre numéro SIREN",
        help_text="Saisissez un numéro SIREN valide, disponible sur le Kbis de votre organisation ou sur l'Annuaire des Entreprises",
        required=True,
    )


class EligibiliteForm(DsfrForm, forms.ModelForm):
    raison_sociale = forms.CharField()

    class Meta:
        model = Entreprise
        fields = ["effectif", "bdese_accord", "raison_sociale", "siren"]
        labels = {
            "bdese_accord": "L'entreprise a un accord collectif d'entreprise concernant la Base de Données Économiques, Sociales et Environnementales (BDESE)"
        }

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
