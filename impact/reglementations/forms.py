from django import forms

from public.forms import DsfrForm
from .models import BDESE_50_300, BDESE_300


class CategoryJSONWidget(forms.MultiWidget):
    template_name = "snippets/category_json_widget.html"

    def __init__(self, categories, widgets=None, attrs=None):
        self.categories = categories
        super().__init__(widgets, attrs)

    def decompress(self, value):
        if type(value) != dict:
            return []
        return [value.get(category) for category in self.categories]


def bdese_form_factory(
    categories_professionnelles, instance, fetched_data=None, *args, **kwargs
):
    class CategoryMultiValueField(forms.MultiValueField):
        widget = CategoryJSONWidget

        def __init__(
            self,
            base_field=forms.IntegerField,
            categories=None,
            encoder=None,
            decoder=None,
            *args,
            **kwargs
        ):
            """https://docs.djangoproject.com/en/4.1/ref/forms/fields/#django.forms.MultiValueField.require_all_fields"""
            self.categories = categories or categories_professionnelles
            fields = [base_field() for category in self.categories]
            widgets = [
                base_field.widget({"label": category}) for category in self.categories
            ]
            super().__init__(
                fields=fields,
                widget=CategoryJSONWidget(
                    self.categories, widgets, attrs={"class": "fr-input"}
                ),
                require_all_fields=False,
                *args,
                **kwargs
            )

        def compress(self, data_list):
            if data_list:
                return dict(zip(self.categories, data_list))
            return None

    class BDESEForm(forms.ModelForm, DsfrForm):
        class Meta:
            model = instance.__class__
            exclude = ["annee", "entreprise"]
            field_classes = {
                category_field: CategoryMultiValueField
                for category_field in BDESE_300.category_fields()
            }

        def __init__(self, fetched_data=None, *args, **kwargs):
            if fetched_data:
                if "initial" not in kwargs:
                    kwargs["initial"] = {}
                kwargs["initial"].update(fetched_data)
            super().__init__(*args, **kwargs)
            if fetched_data:
                for field in fetched_data:
                    if field in self.fields:
                        self.fields[
                            field
                        ].help_text += " (valeur extraite de Index EgaPro)"
                        self.fields[field].disabled = True

    return BDESEForm(fetched_data, *args, **kwargs)
