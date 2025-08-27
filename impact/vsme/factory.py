import json
import os

from django import forms

from utils.forms import DsfrForm
from utils.forms import DsfrFormSet


def load_json_schema(file_path):
    # Get the directory of the current file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Join the current directory with the provided file path
    full_path = os.path.join(current_dir, file_path)
    with open(full_path, "r") as file:
        return json.load(file)


def create_form_from_schema(schema, indicateur_id):
    class _DynamicForm(DsfrForm):
        pass

    fields = schema[indicateur_id]["fields"]
    for field in fields:
        field_type = field["type"]
        field_name = field["name"]
        field_kwargs = {
            "label": field.get("label", field_name),
            "required": field.get("required", True),
            # ...
        }

        # Gestion des arguments spécifiques au type de champ
        match field_type:
            case "text":
                field_kwargs["max_length"] = field.get("max_length", 255)
                _DynamicForm.base_fields[field_name] = forms.CharField(**field_kwargs)
            case "email":
                _DynamicForm.base_fields[field_name] = forms.EmailField(**field_kwargs)
            case "number":
                field_kwargs["min_value"] = field.get("min")
                field_kwargs["max_value"] = field.get("max")
                _DynamicForm.base_fields[field_name] = forms.IntegerField(
                    **field_kwargs
                )
            case "boolean":
                _DynamicForm.base_fields[field_name] = forms.BooleanField(
                    **field_kwargs
                )
            case "choice":
                field_kwargs["choices"] = (
                    (choice["name"], choice["label"]) for choice in field["choices"]
                )
                _DynamicForm.base_fields[field_name] = forms.ChoiceField(**field_kwargs)
            case "table":

                class TableauFormSet(DsfrFormSet):
                    def add_fields(self, form, index):
                        super().add_fields(form, index)
                        for column in field["columns"]:
                            field_name = column["name"]
                            field_kwargs = {
                                "label": column.get("label", field_name),
                                "required": column.get("required", True),
                            }
                            match column["type"]:
                                case "text":
                                    form.fields[field_name] = forms.CharField(
                                        **field_kwargs
                                    )
                                case "number":
                                    form.fields[field_name] = forms.IntegerField(
                                        **field_kwargs
                                    )
                                case "choice":
                                    field_kwargs["choices"] = (
                                        (choice["name"], choice["label"])
                                        for choice in column["choices"]
                                    )
                                    form.fields[field_name] = forms.ChoiceField(
                                        **field_kwargs
                                    )
                                case _:
                                    raise Exception(f"Typo {column["type"]}")

                FormSet = forms.formset_factory(
                    _DynamicForm, formset=TableauFormSet, extra=1
                )
                FormSet.indicator_type = "table"
                return FormSet
        # et on continue ...

    return _DynamicForm
