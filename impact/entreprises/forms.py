from django import forms
from django.core.exceptions import ValidationError

from .models import CaracteristiquesAnnuelles
from utils.forms import DateInput
from utils.forms import DsfrForm


class SirenField(forms.CharField):
    def __init__(self, *args, **kwargs):
        if not kwargs.get("label"):
            kwargs["label"] = "Votre numéro SIREN"
        if not kwargs.get("help_text"):
            kwargs[
                "help_text"
            ] = "Saisissez un numéro SIREN valide, disponible sur le Kbis de votre organisation ou sur l'Annuaire des Entreprises"
        kwargs["min_length"] = 9
        kwargs["max_length"] = 9
        super().__init__(*args, **kwargs)

    def validate(self, value):
        super().validate(value)
        try:
            int(value)
        except ValueError:
            raise ValidationError("Le siren est incorrect")


class EntrepriseAttachForm(DsfrForm):
    siren = SirenField()
    fonctions = forms.CharField(label="Fonction(s) dans la société")


class EntrepriseDetachForm(DsfrForm):
    siren = SirenField()


class EntrepriseQualificationForm(DsfrForm, forms.ModelForm):
    class Meta:
        model = CaracteristiquesAnnuelles
        fields = [
            "date_cloture_exercice",
            "effectif",
            "effectif_outre_mer",
            "tranche_chiffre_affaires",
            "tranche_bilan",
            "bdese_accord",
            "systeme_management_energie",
        ]
        labels = {
            "date_cloture_exercice": "Date de clôture du dernier exercice comptable",
        }
        help_texts = {
            "tranche_chiffre_affaires": "Sélectionnez le chiffre d'affaires de l'exercice clos",
            "tranche_bilan": "Sélectionnez le bilan de l'exercice clos",
        }
        widgets = {
            "systeme_management_energie": forms.CheckboxInput,
            "date_cloture_exercice": DateInput,
        }
