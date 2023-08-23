from django import forms
from django.core.exceptions import ValidationError

from entreprises.forms import SirenField
from entreprises.models import DENOMINATION_MAX_LENGTH
from entreprises.models import Entreprise
from utils.forms import DateInput
from utils.forms import DsfrForm


class SirenForm(DsfrForm):
    siren = SirenField()


class EntrepriseForm(DsfrForm, forms.ModelForm):
    denomination = forms.CharField()

    class Meta:
        model = Entreprise
        fields = [
            "denomination",
            "siren",
            "date_cloture_exercice",
            "appartient_groupe",
            "comptes_consolides",
        ]
        labels = {
            "appartient_groupe": "L'entreprise appartient à un groupe composé d'une société-mère et d'une ou plusieurs filiales",
        }
        widgets = {
            "date_cloture_exercice": DateInput,
            "appartient_groupe": forms.CheckboxInput,
            "comptes_consolides": forms.CheckboxInput,
        }

    def clean_denomination(self):
        denomination = self.cleaned_data.get("denomination")
        return denomination[:DENOMINATION_MAX_LENGTH]


class NaiveCaptchaField(forms.CharField):
    def validate(self, value):
        super().validate(value)
        try:
            int(value)
            raise ValidationError("La réponse doit être écrite en toutes lettres")
        except ValueError:
            pass
        if value.lower() != "trois":
            raise ValidationError("La somme est incorrecte")


class ContactForm(DsfrForm):
    email = forms.EmailField(label="Votre adresse e-mail")
    subject = forms.CharField(
        label="Sujet",
        max_length=255,
    )
    message = forms.CharField(widget=forms.Textarea())
    sum = NaiveCaptchaField(
        label="Pour vérifier que vous n'êtes pas un robot, merci de répondre en toutes lettres à la question 1 + 2 = ?",
        max_length=10,
    )
