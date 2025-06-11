from django import forms
from django.contrib import admin

from reglementations.models import BDESE_300
from reglementations.models import BDESE_50_300
from reglementations.models import BDESEAvecAccord
from reglementations.models import CategoryType
from reglementations.models.csrd import DocumentAnalyseIA
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


@admin.register(RapportCSRD)
class RapportCSRDAdmin(admin.ModelAdmin):
    pass


@admin.register(DocumentAnalyseIA)
class DocumentAnalyseIA_Admin(admin.ModelAdmin):
    list_display = ["nom", "rapport_csrd"]
    search_fields = (
        "nom",
        "rapport_csrd__entreprise__denomination",
        "rapport_csrd__entreprise__siren",
    )
    readonly_fields = ("nombre_de_phrases_pertinentes",)
