from django.contrib import admin
from django import forms

from .models import Entreprise


class EntrepriseAdmin(admin.ModelAdmin):
    list_display = ["siren", "raison_sociale"]


admin.site.register(Entreprise, EntrepriseAdmin)
