from django import forms
from django.contrib import admin

from reglementations.models import BDESE_300
from reglementations.models import BDESE_50_300
from reglementations.models import CategoryType
from reglementations.models import OfficialBDESE_300
from reglementations.models import OfficialBDESE_50_300
from reglementations.models import OfficialBDESEAvecAccord
from reglementations.models import PersonalBDESE_300
from reglementations.models import PersonalBDESE_50_300
from reglementations.models import PersonalBDESEAvecAccord
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


@admin.register(PersonalBDESE_300, PersonalBDESE_50_300, PersonalBDESEAvecAccord)
class PersonalBDESE_Admin(admin.ModelAdmin):
    form = BDESEAdminForm
    list_display = ["entreprise", "annee", "user"]
    list_filter = (("user", admin.RelatedOnlyFieldListFilter),)


@admin.register(OfficialBDESE_300, OfficialBDESE_50_300, OfficialBDESEAvecAccord)
class OfficialBDESE_Admin(admin.ModelAdmin):
    form = BDESEAdminForm
    list_display = ["entreprise", "annee"]


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
