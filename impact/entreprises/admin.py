from django.contrib import admin
from django import forms

from entreprises.models import Entreprise
from habilitations.admin import HabilitationInline


class EntrepriseAdmin(admin.ModelAdmin):
    list_display = ["siren", "raison_sociale"]
    inlines = (HabilitationInline,)


admin.site.register(Entreprise, EntrepriseAdmin)
