from django import forms
from django.contrib import admin

from entreprises.models import Entreprise
from habilitations.admin import HabilitationInline


class EntrepriseAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["effectif"].required = False


class EntrepriseAdmin(admin.ModelAdmin):
    list_display = ["siren", "raison_sociale"]
    inlines = (HabilitationInline,)
    model = Entreprise
    form = EntrepriseAdminForm


admin.site.register(Entreprise, EntrepriseAdmin)
