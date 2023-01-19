from django import forms

from entreprises.models import Entreprise, RAISON_SOCIALE_MAX_LENGTH


class DsfrForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if type(field.widget) == forms.widgets.Select:
                fr_name = "fr-select"
            else:
                fr_name = "fr-input"
            field.widget.attrs.update({"class": f"{fr_name}"})
            if name in self.errors:
                field.widget.attrs.update(
                    {
                        "class": f"{fr_name} {fr_name}-error",
                        "aria-describedby": f"{name}-error-desc-error",
                    }
                )


class SirenForm(DsfrForm):
    siren = forms.CharField(
        label="Votre numéro SIREN",
        help_text="Saisissez un numéro SIREN valide, disponible sur le Kbis de votre organisation",
        required=True,
        min_length=9,
        max_length=9,
    )


class EligibiliteForm(DsfrForm, forms.ModelForm):
    raison_sociale = forms.CharField()

    class Meta:
        model = Entreprise
        fields = ["effectif", "bdese_accord", "raison_sociale", "siren"]
        labels = {
            "bdese_accord": "L'entreprise a un accord collectif d'entreprise concernant la Base de Données Économiques, Sociales et Environnementales (BDESE)"
        }

    def clean_raison_sociale(self):
        raison_sociale = self.cleaned_data.get("raison_sociale")
        return raison_sociale[:RAISON_SOCIALE_MAX_LENGTH]


class ContactForm(DsfrForm):
    email = forms.EmailField(label="Votre email")
    subject = forms.CharField(
        label="Sujet",
        max_length=255,
    )
    message = forms.CharField(widget=forms.Textarea())
