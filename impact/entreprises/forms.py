from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator, MaxLengthValidator

from utils.forms import DsfrForm
from .models import Entreprise


class SirenField(forms.CharField):
    def validate(self, value):
        super().validate(value)
        MinLengthValidator(9)(value)
        MaxLengthValidator(9)(value)
        try:
            int(value)
        except ValueError:
            raise ValidationError("Le siren est incorrect")


class EntrepriseAddForm(DsfrForm):
    siren = SirenField(
        label="Numéro SIREN",
        help_text="Saisissez un numéro SIREN valide, disponible sur le Kbis de votre organisation",
    )
    fonctions = forms.CharField(label="Fonction(s) dans la société")


class EntrepriseQualificationForm(forms.ModelForm, DsfrForm):
    class Meta:
        model = Entreprise
        fields = ["effectif", "bdese_accord"]
