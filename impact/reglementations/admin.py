from django import forms
from django.contrib import admin

from reglementations.models import BDESE_300
from reglementations.models import BDESE_50_300
from reglementations.models import BDESEAvecAccord
from reglementations.models import CategoryType
from reglementations.models.csrd import RapportCSRD


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


@admin.register(BDESE_300, BDESE_50_300, BDESEAvecAccord)
class BDESE_Admin(admin.ModelAdmin):
    form = BDESEAdminForm
    list_display = ["entreprise", "annee", "user"]
    list_filter = (("user", admin.EmptyFieldListFilter),)
    search_fields = ("user__email", "entreprise__denomination", "entreprise__siren")
    raw_id_fields = ("user", "entreprise")


@admin.register(RapportCSRD)
class RapportCSRDAdmin(admin.ModelAdmin):
    list_display = ["entreprise", "annee", "proprietaire"]
    list_filter = (("proprietaire", admin.EmptyFieldListFilter),)
    search_fields = (
        "proprietaire__email",
        "entreprise__denomination",
        "entreprise__siren",
    )
    raw_id_fields = ("proprietaire", "entreprise")
