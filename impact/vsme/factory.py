from django import forms

from utils.forms import DsfrForm
from utils.forms import DsfrFormSet
from vsme.models import EXIGENCES_DE_PUBLICATION


def create_form_from_schema(schema, **kwargs):
    class _DynamicForm(DsfrForm):
        pass

    fields = schema["fields"]
    for field in fields:
        field_name = field["name"]
        field_type = field["type"]

        match field_type:
            case "text" | "number" | "boolean" | "choice":
                _DynamicForm.base_fields[field_name] = create_simple_field_from_schema(
                    field
                )
            case "table":

                class TableauFormSet(DsfrFormSet):
                    def add_fields(self, form, index):
                        super().add_fields(form, index)
                        for column in field["columns"]:
                            field_name = column["name"]
                            form.fields[field_name] = create_simple_field_from_schema(
                                column
                            )

                    @property
                    def cleaned_data(self):
                        super().cleaned_data
                        # surcharge cleaned_data pour supprimer les valeurs des lignes supprimées
                        return [
                            form.cleaned_data
                            for form in self.forms
                            if form not in self.deleted_forms
                        ]

                extra = kwargs.get("extra", 0)
                FormSet = forms.formset_factory(
                    _DynamicForm, formset=TableauFormSet, extra=extra, can_delete=True
                )  # TODO: ajouter les params django min_num et validate_min pour ne pas enregistrer de valeur nulle ?
                FormSet.indicator_type = "table"
                return FormSet
            case "exigences_de_publication":
                field["type"] = "multiple_choice"
                choices = [
                    (id, f"{id} - {nom}")
                    for id, nom in EXIGENCES_DE_PUBLICATION.items()
                ]
                _DynamicForm.base_fields[field_name] = create_simple_field_from_schema(
                    field, choices=choices
                )

    return _DynamicForm


def create_simple_field_from_schema(field_schema, **kwargs):
    field_name = field_schema["name"]
    field_kwargs = {
        "label": field_schema.get("label", field_name),
        "required": field_schema.get("required", False),
        # ...
    }
    match field_schema["type"]:
        case "text":
            field_kwargs["max_length"] = field_schema.get("max_length", 255)
            return forms.CharField(**field_kwargs)
        case "number":
            field_kwargs["min_value"] = field_schema.get("min")
            field_kwargs["max_value"] = field_schema.get("max")
            return forms.IntegerField(**field_kwargs)
        case "boolean":
            return forms.BooleanField(**field_kwargs)
        case "choice":
            field_kwargs["choices"] = (
                (choice["name"], choice["label"]) for choice in field_schema["choices"]
            )
            return forms.ChoiceField(**field_kwargs)
        case "multiple_choice":
            choices = kwargs.get("choices") or (
                (choice["name"], choice["label"]) for choice in field_schema["choices"]
            )
            return forms.MultipleChoiceField(
                widget=forms.CheckboxSelectMultiple,
                choices=choices,
                **field_kwargs,
            )
        case _:
            raise Exception(f"Type inconnu : {field_type}")
