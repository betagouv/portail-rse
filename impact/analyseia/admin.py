from django.contrib import admin

from analyseia.models import AnalyseIA


@admin.register(AnalyseIA)
class AnalyseIA_Admin(admin.ModelAdmin):
    readonly_fields = ("nombre_de_phrases_pertinentes", "entreprise")
