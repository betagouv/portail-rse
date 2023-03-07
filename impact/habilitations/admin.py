from django.contrib import admin

from .models import Habilitation


from django.contrib import admin


@admin.action(description="Confirmer les habilitations")
def confirm_habilitations(modeladmin, request, queryset):
    for habilitation in queryset:
        if not habilitation.is_confirmed:
            habilitation.confirm()
            habilitation.save()


class HabilitationAdmin(admin.ModelAdmin):
    list_display = ["user", "entreprise", "is_confirmed"]
    readonly_fields = ["confirmed_at"]
    actions = [confirm_habilitations]


admin.site.register(Habilitation, HabilitationAdmin)
