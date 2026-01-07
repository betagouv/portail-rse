from django.contrib import admin

from .models import Indicateur
from .models import RapportVSME


class IndicateurInline(admin.TabularInline):
    model = Indicateur
    readonly_fields = (
        "schema_id",
        "schema_version",
        "_data",
    )
    extra = 0


class RapportVSMEAdmin(admin.ModelAdmin):
    raw_id_fields = ("entreprise",)
    inlines = (IndicateurInline,)
    search_fields = (
        "entreprise__denomination",
        "entreprise__siren",
    )
    list_display = ("id", "entreprise", "annee")


admin.site.register(RapportVSME, RapportVSMEAdmin)
