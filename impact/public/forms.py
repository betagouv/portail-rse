from django import forms
from django.core.exceptions import ValidationError

from entreprises.forms import EntrepriseForm
from entreprises.forms import SirenField
from entreprises.models import CaracteristiquesAnnuelles
from entreprises.models import DENOMINATION_MAX_LENGTH
from utils.forms import DsfrForm


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
        label="Objet",
        max_length=255,
    )
    message = forms.CharField(
        label="Comment peut-on vous aider ?",
        widget=forms.Textarea(),
        help_text="Pour nous permettre de vous aider au mieux et de traiter votre demande plus rapidement, merci de bien détailler votre situation : contexte, étapes déjà effectuées, messages d'erreur éventuels, etc. Si votre entreprise est déjà inscrite sur le Portail RSE, merci d'indiquer votre numéro SIREN dans votre message.",
    )
    sum = NaiveCaptchaField(
        label="Pour vérifier que vous n'êtes pas un robot, merci de répondre en toutes lettres à la question 1 + 2 = ?",
        max_length=10,
    )


class SimulationForm(EntrepriseForm, forms.ModelForm):
    denomination = forms.CharField()
    siren = SirenField()
    categorie_juridique_sirene = forms.IntegerField()
    code_pays_etranger_sirene = forms.IntegerField(required=False)
    code_NAF = forms.CharField(required=False)

    class Meta:
        model = CaracteristiquesAnnuelles
        fields = [
            "effectif",
            "effectif_groupe",
            "tranche_chiffre_affaires",
            "tranche_bilan",
            "tranche_chiffre_affaires_consolide",
            "tranche_bilan_consolide",
        ]
        labels = {
            "effectif": "Effectif",
            "effectif_groupe": "Effectif du groupe",
        }
        help_texts = {
            "effectif": "Vérifiez et confirmez le nombre de salariés de l'entreprise",
            "effectif_groupe": "Nombre de salariés du groupe",
            "tranche_chiffre_affaires": "Montant net du chiffre d'affaires de l'exercice clos",
            "tranche_bilan": "Total du bilan de l'exercice clos",
            "tranche_chiffre_affaires_consolide": "Montant net du chiffre d'affaires consolidé de l'exercice clos",
            "tranche_bilan_consolide": "Total du bilan consolidé de l'exercice clos",
        }

    def clean_denomination(self):
        denomination = self.cleaned_data.get("denomination")
        return denomination[:DENOMINATION_MAX_LENGTH]
