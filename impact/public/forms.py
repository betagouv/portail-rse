from django import forms

from .models import BDESE


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


class EligibiliteForm(DsfrForm):
    effectif = forms.ChoiceField(
        label="Votre effectif total",
        choices=(
            ("petit", "moins de 50"),
            ("moyen", "entre 50 et 300"),
            ("grand", "plus de 300"),
        ),
        help_text="Saisissez le nombre de salariés",
        required=True,
    )
    accord = forms.BooleanField(
        label="Avez-vous un accord collectif d'entreprise concernant le BDESE ?",
        help_text="",
        required=False,
    )
    raison_sociale = forms.CharField()


class BDESEForm(forms.ModelForm, DsfrForm):
    class Meta:
        model = BDESE
        exclude = ["year"]
