from django import forms

from entreprises.models import Entreprise


class DsfrForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if type(field.widget) == forms.widgets.Select:
                field.widget.attrs.update({"class": "fr-select"})
            else:
                field.widget.attrs.update({"class": "fr-input"})


class SirenForm(DsfrForm):
    siren = forms.CharField(
        label="Votre numéro SIREN",
        help_text="Saisissez un numéro SIREN valide, disponible sur le Kbis de votre organisation",
        required=True,
        min_length=9,
        max_length=9,
    )


class EligibiliteForm(DsfrForm, forms.ModelForm):
    class Meta:
        model = Entreprise
        fields = ["effectif", "bdese_accord", "raison_sociale", "siren"]
        labels = {
            "bdese_accord": "Avez-vous un accord collectif d'entreprise concernant la BDESE ?"
        }
