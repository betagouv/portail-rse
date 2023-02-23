from django import forms
from public.forms import DsfrForm
from .models import Entreprise


class EntrepriseCreationForm(DsfrForm):

    siren = forms.CharField(
        label="Numéro SIREN",
        help_text="Saisissez un numéro SIREN valide, disponible sur le Kbis de votre organisation",
        min_length=9,
        max_length=9,
    )
    fonctions = forms.CharField(label="Fonction(s) dans la société")
