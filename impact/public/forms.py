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


class CategoryJSONWidget(forms.MultiWidget):
    template_name = "snippets/category_json_widget.html"

    def __init__(self, categories, widgets=None, attrs=None):
        self.categories = categories
        super().__init__(widgets, attrs)


    def get_context(self, name, value, attrs=None):
       context = super().get_context(name, value, attrs)
       context["categories"] = list(self.categories.keys())
       return context

    def decompress(self, value):
        if type(value) != dict:
            return []
        return [value.get(category) for category in self.categories]


class CategoryJSONField(forms.MultiValueField):
    widget = CategoryJSONWidget

    def __init__(self, base_field, categories, *args, **kwargs):
        """https://docs.djangoproject.com/en/4.1/ref/forms/fields/#django.forms.MultiValueField.require_all_fields"""
        self.categories = categories
        fields = [
            base_field() for category in categories
        ]
        widgets = [base_field.widget for category in categories]
        super().__init__(
            fields=fields,
            widget=CategoryJSONWidget(categories, widgets, attrs={"class": "fr-input"}),
            require_all_fields=False, *args, **kwargs
        )

    def compress(self, data_list):
        if data_list:
            return dict(zip(self.categories, data_list))
        return None


def default_json_categories():
    return {categorie: None for categorie in categories_default()}


class BDESEForm(forms.ModelForm, DsfrForm):
    #effectif_total = CategoryField(forms.IntegerField(), 5, categories=categories_default())
    effectif_total = CategoryJSONField(forms.IntegerField, default_json_categories())
    class Meta:
        model = BDESE
        exclude = ["annee"]
