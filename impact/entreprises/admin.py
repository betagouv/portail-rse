from django import forms
from django.contrib import admin

from entreprises.models import Entreprise
from entreprises.models import Evolution
from habilitations.admin import HabilitationInline


class EntrepriseAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class EntrepriseAdmin(admin.ModelAdmin):
    list_display = ["siren", "denomination"]
    inlines = (HabilitationInline,)
    model = Entreprise
    form = EntrepriseAdminForm


class EvolutionAdmin(admin.ModelAdmin):
    list_display = ["entreprise", "annee"]
    model = Evolution


admin.site.register(Entreprise, EntrepriseAdmin)
admin.site.register(Evolution, EvolutionAdmin)
