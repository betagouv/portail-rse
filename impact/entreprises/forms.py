from django import forms
from public.forms import DsfrForm
from .models import Entreprise


class EntrepriseCreationForm(DsfrForm, forms.ModelForm):

    class Meta:
        model = Entreprise
        fields = ("siren",)

    siren = forms.CharField(
        label="Numéro SIREN",
        help_text="Saisissez un numéro SIREN valide, disponible sur le Kbis de votre organisation",
        min_length=9,
        max_length=9,
    )