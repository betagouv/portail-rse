from django import forms
from django.contrib import admin

from reglementations.models import (
    BDESE_300,
    BDESE_50_300,
    CategoryType,
    OfficialBDESE_300,
    OfficialBDESE_50_300,
    PersonalBDESE_300,
    PersonalBDESE_50_300,
)


class CategoryJSONField(forms.JSONField):
    def __init__(
        self,
        base_field=forms.IntegerField,
        category_type=CategoryType.HARD_CODED,
        categories=None,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)


class BDESEAdminForm(forms.ModelForm):
    class Meta:
        fields = "__all__"
        field_classes = {
            category_field: CategoryJSONField
            for category_field in BDESE_300.category_fields()
            + BDESE_50_300.category_fields()
        }


@admin.register(PersonalBDESE_300, PersonalBDESE_50_300)
class PersonalBDESE_Admin(admin.ModelAdmin):
    form = BDESEAdminForm
    list_display = ["entreprise", "annee", "user"]
    list_filter = (("user", admin.RelatedOnlyFieldListFilter),)


@admin.register(OfficialBDESE_300, OfficialBDESE_50_300)
class OfficialBDESE_Admin(admin.ModelAdmin):
    form = BDESEAdminForm
    list_display = ["entreprise", "annee"]
