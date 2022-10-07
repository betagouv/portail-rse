from django.contrib import admin
from django import forms

from .models import BDESE, Entreprise


class CategoryJSONField(forms.JSONField):
    def __init__(self, base_field=forms.IntegerField, categories=None, *args, **kwargs):
        super().__init__(*args, **kwargs)


class BDESEForm(forms.ModelForm):
    class Meta:
        model = BDESE
        fields = "__all__"
        field_classes = {
            category_field: CategoryJSONField
            for category_field in BDESE.category_fields()
        }


@admin.register(BDESE)
class BDESEAdmin(admin.ModelAdmin):
    form = BDESEForm


admin.site.register(Entreprise)
