from django import forms
from django.contrib.postgres.forms import SplitArrayField, SplitArrayWidget

from .models import BDESE, categories_default


class DsfrForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if type(field.widget) == forms.widgets.Select:
                field.widget.attrs.update({"class": "fr-select"})
            else:
                field.widget.attrs.update({"class": "fr-input"})


class SirenForm(DsfrForm):
    siren = forms.CharField(
        label="Votre numéro SIREN",
        help_text="Saisissez un numéro SIREN valide, disponible sur le Kbis de votre organisation",
        required=True,
        min_length=9,
        max_length=9,
    )


class EligibiliteForm(DsfrForm):
    effectif = forms.ChoiceField(
        label="Votre effectif total",
        choices=(
            ("petit", "moins de 50"),
            ("moyen", "entre 50 et 300"),
            ("grand", "entre 301 et 499"),
            ("sup500", "500 et plus"),
        ),
        help_text="Saisissez le nombre de salariés",
        required=True,
    )
    accord = forms.BooleanField(
        label="Avez-vous un accord collectif d'entreprise concernant le BDESE ?",
        help_text="",
        required=False,
    )
    raison_sociale = forms.CharField()


class CategoryWidget(SplitArrayWidget):
    template_name = "snippets/category_widget.html"

    def __init__(self, categories, *args, **kwargs):
        self.categories = categories
        super().__init__(*args, **kwargs)

    
    def get_context(self, name, value, attrs=None):
        context = super().get_context(name, value, {"class": "fr-input"})
        context["categories"] = self.categories
        return context


class CategoryField(SplitArrayField):
    def __init__(self, base_field, size, categories, *args, **kwargs):
        widget = CategoryWidget(categories=categories, widget=base_field.widget, size=size)
        super().__init__(base_field, size, *args, widget=widget)


class BDESEForm(forms.ModelForm, DsfrForm):
    effectif_total = CategoryField(forms.IntegerField(), 5, categories=categories_default())
    class Meta:
        model = BDESE
        exclude = ["annee"]
