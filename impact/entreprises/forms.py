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


class EntrepriseForm(DsfrForm):
    appartient_groupe = forms.BooleanField(
        required=False,
        label="L'entreprise appartient à un groupe composé d'une société-mère et d'une ou plusieurs filiales",
    )
    comptes_consolides = forms.BooleanField(
        required=False,
        label="Le groupe d'entreprises établit des comptes consolidés",
    )

    def clean(self):
        cleaned_data = super().clean()
        appartient_groupe = cleaned_data.get("appartient_groupe")
        if not appartient_groupe:
            cleaned_data["comptes_consolides"] = False
        comptes_consolides = cleaned_data.get("comptes_consolides")
        tranche_chiffre_affaires_consolide = cleaned_data.get(
            "tranche_chiffre_affaires_consolide"
        )
        tranche_bilan_consolide = cleaned_data.get("tranche_bilan_consolide")
        if comptes_consolides:
            ERREUR = "Ce champ est obligatoire lorsque les comptes sont consolidés"
            if not tranche_chiffre_affaires_consolide:
                self.add_error("tranche_chiffre_affaires_consolide", ERREUR)
            if not tranche_bilan_consolide:
                self.add_error("tranche_bilan_consolide", ERREUR)
        else:
            if tranche_chiffre_affaires_consolide:
                cleaned_data["tranche_chiffre_affaires_consolide"] = None
            if tranche_bilan_consolide:
                cleaned_data["tranche_bilan_consolide"] = None


class EntrepriseQualificationForm(EntrepriseForm, forms.ModelForm):
    class Meta:
        model = CaracteristiquesAnnuelles
        fields = [
            "date_cloture_exercice",
            "effectif",
            "effectif_outre_mer",
            "tranche_chiffre_affaires",
            "tranche_bilan",
            "tranche_chiffre_affaires_consolide",
            "tranche_bilan_consolide",
            "bdese_accord",
            "systeme_management_energie",
        ]
        labels = {
            "date_cloture_exercice": "Date de clôture du dernier exercice comptable",
            "systeme_management_energie": "L'entreprise a mis en place un <a target='_blank' href='https://agirpourlatransition.ademe.fr/entreprises/demarche-decarbonation-industrie/agir/structurer-demarche/mettre-en-place-systeme-management-energie'>système de management de l’énergie</a>",
        }
        help_texts = {
            "tranche_chiffre_affaires": "Sélectionnez le chiffre d'affaires de l'exercice clos",
            "tranche_bilan": "Sélectionnez le bilan de l'exercice clos",
        }
        widgets = {
            "bdese_accord": forms.CheckboxInput,
            "systeme_management_energie": forms.CheckboxInput,
            "date_cloture_exercice": DateInput,
        }
