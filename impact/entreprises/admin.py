from django import forms
from django.contrib import admin

from entreprises.models import CaracteristiquesAnnuelles
from entreprises.models import Entreprise
from habilitations.admin import HabilitationInline


class EntrepriseAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["date_cloture_exercice"].required = False


class CaracteristiquesAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].required = False


class CaracteristiquesInline(admin.TabularInline):
    model = CaracteristiquesAnnuelles
    extra = 0
    form = CaracteristiquesAdminForm


class UsersFilter(admin.SimpleListFilter):
    title = "Avec utilisateur"
    parameter_name = "avec_utilisateur"

    def lookups(self, request, model_admin):
        return [("1", "Oui"), ("0", "Non")]

    def queryset(self, request, queryset):
        if self.value() == "1":
            return queryset.filter(habilitation__isnull=False).distinct()
        if self.value() == "0":
            return queryset.filter(habilitation__isnull=True).distinct()


class EntrepriseAdmin(admin.ModelAdmin):
    list_display = ["siren", "denomination"]
    inlines = (HabilitationInline, CaracteristiquesInline)
    model = Entreprise
    form = EntrepriseAdminForm
    search_fields = ("denomination", "siren")
    list_filter = (UsersFilter,)


admin.site.register(Entreprise, EntrepriseAdmin)
