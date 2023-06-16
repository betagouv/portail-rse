from django import forms
from django.core.exceptions import ValidationError

from entreprises.forms import SirenField
from entreprises.models import CaracteristiquesAnnuelles
from entreprises.models import DENOMINATION_MAX_LENGTH
from entreprises.models import Entreprise
from utils.forms import DsfrForm


class SirenForm(DsfrForm):
    siren = SirenField()


class EntrepriseForm(DsfrForm, forms.ModelForm):
    class Meta:
        model = Entreprise
        fields = ["denomination", "siren"]

    def clean_denomination(self):
        denomination = self.cleaned_data.get("denomination")
        return denomination[:DENOMINATION_MAX_LENGTH]


class CaracteristiquesForm(DsfrForm, forms.ModelForm):
    class Meta:
        model = CaracteristiquesAnnuelles
        fields = ["effectif", "bdese_accord"]


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
