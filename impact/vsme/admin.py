from django.contrib import admin

from .models import RapportVSME


class RapportVSMEAdmin(admin.ModelAdmin):
    raw_id_fields = ("entreprise",)


admin.site.register(RapportVSME, RapportVSMEAdmin)
