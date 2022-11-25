from django import forms
from django.contrib import admin

from .models import BDESE_300, BDESE_50_300


class CategoryJSONField(forms.JSONField):
    def __init__(self, base_field=forms.IntegerField, categories=None, *args, **kwargs):
        super().__init__(*args, **kwargs)


class BDESE_300Form(forms.ModelForm):
    class Meta:
        model = BDESE_300
        fields = "__all__"
        field_classes = {
            category_field: CategoryJSONField
            for category_field in BDESE_300.category_fields()
        }


class BDESE_50_300Form(forms.ModelForm):
    class Meta:
        model = BDESE_50_300
        fields = "__all__"
        field_classes = {
            category_field: CategoryJSONField
            for category_field in BDESE_50_300.category_fields()
        }


@admin.register(BDESE_300)
class BDESE_300Admin(admin.ModelAdmin):
    form = BDESE_300Form
    list_display = ["entreprise", "annee"]


@admin.register(BDESE_50_300)
class BDESE_50_300Admin(admin.ModelAdmin):
    form = BDESE_50_300Form
    list_display = ["entreprise", "annee"]
