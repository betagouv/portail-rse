from django.contrib import admin
from django import forms

from .models import Entreprise
from habilitations.models import Habilitation


class HabilitationInline(admin.TabularInline):
    model = Habilitation
    extra = 1


class EntrepriseAdmin(admin.ModelAdmin):
    list_display = ["siren", "raison_sociale"]
    inlines = (HabilitationInline,)


admin.site.register(Entreprise, EntrepriseAdmin)
