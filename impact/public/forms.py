from django import forms


class SirenForm(forms.Form):
    siren = forms.CharField(
        label="Votre numéro de SIREN",
        help_text="Saisissez un numéro SIREN valide, disponible sur le Kbis de votre organisation",
        required=True,
        min_length=9,
        max_length=9,
    )
    siren.widget.attrs.update({"class": "fr-input"})


class EligibiliteForm(forms.Form):
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
    effectif.widget.attrs.update({"class": "fr-select"})
    accord = forms.BooleanField(
        label="Avez-vous un accord collectif d'entreprise concernant le BDESE ?",
        help_text="",
        required=False,
    )
