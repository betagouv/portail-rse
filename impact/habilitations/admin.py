from django.contrib import admin

from habilitations.models import Habilitation


class HabilitationInline(admin.TabularInline):
    model = Habilitation
    raw_id_fields = ("user", "entreprise", "invitation")
    extra = 0
