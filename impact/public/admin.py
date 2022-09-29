from django.contrib import admin
from django import forms

from .models import BDESE, Entreprise


class CategoryJSONField(forms.JSONField):
    def __init__(self, base_field, *args, **kwargs):
        super().__init__(*args, **kwargs)


class BDESEForm(forms.ModelForm):
    class Meta:
        model = BDESE
        fields = "__all__"
        field_classes = {"effectif_total": CategoryJSONField}


@admin.register(BDESE)
class BDESEAdmin(admin.ModelAdmin):
    form = BDESEForm


admin.site.register(Entreprise)
