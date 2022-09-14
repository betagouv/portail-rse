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
