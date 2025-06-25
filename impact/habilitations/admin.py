from django import forms
from django.contrib import admin

from habilitations.models import Habilitation


class HabilitationAdminForm(forms.ModelForm):
    should_be_confirmed = forms.BooleanField(
        required=False, label="Confirmer l'habilitation"
    )

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
        return habilitation


class HabilitationInline(admin.TabularInline):
    model = Habilitation
    form = HabilitationAdminForm
    readonly_fields = ("confirmed_at",)
    raw_id_fields = ("user", "entreprise", "invitation")
    extra = 0
