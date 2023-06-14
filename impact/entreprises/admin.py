from django import forms
from django.contrib import admin

from entreprises.models import Entreprise
from entreprises.models import Evolution
from habilitations.admin import HabilitationInline


class EntrepriseAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class EvolutionInline(admin.TabularInline):
    model = Evolution
    extra = 0


class EntrepriseAdmin(admin.ModelAdmin):
    list_display = ["siren", "denomination"]
    inlines = (HabilitationInline, EvolutionInline)
    model = Entreprise
    form = EntrepriseAdminForm


admin.site.register(Entreprise, EntrepriseAdmin)
