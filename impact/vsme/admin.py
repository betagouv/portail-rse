from django.contrib import admin

from .models import RapportVSME


class RapportVSMEAdmin(admin.ModelAdmin):
    pass


admin.site.register(RapportVSME, RapportVSMEAdmin)
