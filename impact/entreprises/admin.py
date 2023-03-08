from django.contrib import admin
from django import forms

from .models import Entreprise
from habilitations.models import Habilitation


class HabilitationAdminForm(forms.ModelForm):
    should_be_confirmed = forms.BooleanField(required=False, label="Confirmer ?")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.confirmed_at:
            self.initial["should_be_confirmed"] = True

    def save(self, *args, **kwargs):
        habilitation = super().save(*args, **kwargs)
        if "should_be_confirmed" in self.changed_data:
            if self.cleaned_data["should_be_confirmed"]:
                habilitation.confirm()
            else:
                habilitation.unconfirm()
            habilitation.save()


class HabilitationInline(admin.TabularInline):
    model = Habilitation
    form = HabilitationAdminForm
    readonly_fields = ("confirmed_at",)
    extra = 0


class EntrepriseAdmin(admin.ModelAdmin):
    list_display = ["siren", "raison_sociale"]
    inlines = (HabilitationInline,)


admin.site.register(Entreprise, EntrepriseAdmin)
