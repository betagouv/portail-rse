from django import forms
from django.core.exceptions import ValidationError

from .models import CaracteristiquesAnnuelles
from .models import Entreprise
from utils.forms import DateInput
from utils.forms import DsfrForm


ERREUR_CHAMP_MANQUANT_GROUPE = (
    "Ce champ est obligatoire lorsque l'entreprise appartient à un groupe"
)
ERREUR_CHAMP_MANQUANT_COMPTES_CONSOLIDES = (
    "Ce champ est obligatoire lorsque les comptes sont consolidés"
)


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
    est_cotee = forms.BooleanField(
        required=False,
        label=Entreprise.est_cotee.field.verbose_name,
    )
    appartient_groupe = forms.BooleanField(
        required=False,
        label="L'entreprise fait partie d'un groupe composé d'une société-mère et d'une ou plusieurs filiales",
    )
    est_societe_mere = forms.BooleanField(
        required=False,
        label=Entreprise.est_societe_mere.field.verbose_name,
    )
    comptes_consolides = forms.BooleanField(
        required=False,
        label="Le groupe d'entreprises établit des comptes consolidés",
    )

    def clean(self):
        super().clean()

        appartient_groupe = self.cleaned_data.get("appartient_groupe")
        if appartient_groupe:
            if not self.cleaned_data.get("effectif_groupe"):
                self.add_error("effectif_groupe", ERREUR_CHAMP_MANQUANT_GROUPE)
        else:
            self.cleaned_data["est_societe_mere"] = None
            self.cleaned_data["effectif_groupe"] = None
            self.cleaned_data["comptes_consolides"] = None

        comptes_consolides = self.cleaned_data.get("comptes_consolides")
        tranche_chiffre_affaires_consolide = self.cleaned_data.get(
            "tranche_chiffre_affaires_consolide"
        )
        tranche_bilan_consolide = self.cleaned_data.get("tranche_bilan_consolide")
        if comptes_consolides:
            if not tranche_chiffre_affaires_consolide:
                self.add_error(
                    "tranche_chiffre_affaires_consolide",
                    ERREUR_CHAMP_MANQUANT_COMPTES_CONSOLIDES,
                )
            if not tranche_bilan_consolide:
                self.add_error(
                    "tranche_bilan_consolide", ERREUR_CHAMP_MANQUANT_COMPTES_CONSOLIDES
                )
        else:
            if tranche_chiffre_affaires_consolide:
                self.cleaned_data["tranche_chiffre_affaires_consolide"] = None
            if tranche_bilan_consolide:
                self.cleaned_data["tranche_bilan_consolide"] = None

        return self.cleaned_data


class EntrepriseQualificationForm(EntrepriseForm, forms.ModelForm):
    societe_mere_en_france = forms.BooleanField(
        required=False,
        label=Entreprise.societe_mere_en_france.field.verbose_name,
    )

    class Meta:
        model = CaracteristiquesAnnuelles
        fields = [
            "date_cloture_exercice",
            "effectif",
            "effectif_permanent",
            "effectif_outre_mer",
            "effectif_groupe",
            "effectif_groupe_france",
            "effectif_groupe_permanent",
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
            "tranche_chiffre_affaires": "Montant net du chiffre d'affaires de l'exercice clos",
            "tranche_bilan": "Total du bilan de l'exercice clos",
        }
        widgets = {
            "bdese_accord": forms.CheckboxInput,
            "systeme_management_energie": forms.CheckboxInput,
            "date_cloture_exercice": DateInput,
        }

    def clean(self):
        ERREUR_CHAMP_MANQUANT_GROUPE = (
            "Ce champ est obligatoire lorsque l'entreprise appartient à un groupe"
        )

        super().clean()

        appartient_groupe = self.cleaned_data.get("appartient_groupe")
        if appartient_groupe:
            if not self.cleaned_data.get("effectif_groupe_permanent"):
                self.add_error(
                    "effectif_groupe_permanent", ERREUR_CHAMP_MANQUANT_GROUPE
                )
            if not self.cleaned_data.get("effectif_groupe_france"):
                self.add_error("effectif_groupe_france", ERREUR_CHAMP_MANQUANT_GROUPE)
        else:
            self.cleaned_data["effectif_groupe_france"] = None
            self.cleaned_data["effectif_groupe_permanent"] = None
            self.cleaned_data["societe_mere_en_france"] = None

        return self.cleaned_data
