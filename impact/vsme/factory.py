import os

import yaml
from django import forms


def load_yaml_schema(file_path):
    # Get the directory of the current file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Join the current directory with the provided file path
    full_path = os.path.join(current_dir, file_path)
    with open(full_path, "r") as file:
        return yaml.safe_load(file)


def create_form_from_yaml(yaml_data, indicateur_id):
    class _DynamicForm(forms.Form):
        pass

    fields = yaml_data["indicators"][indicateur_id]["fields"]
    for field in fields:
        field_type = field["type"]
        field_name = field["name"]
        field_kwargs = {
            "label": field.get("label", field_name),
            "required": field.get("required", True),
            # ...
        }

        # Gestion des arguments spécifiques au type de champ
        if field_type == "text":
            field_kwargs["max_length"] = field.get("max_length", 255)
            field_kwargs["widget"] = forms.TextInput(
                attrs={"class": "fr-input"},
            )
            _DynamicForm.base_fields[field_name] = forms.CharField(**field_kwargs)
        elif field_type == "email":
            field_kwargs["widget"] = forms.TextInput(
                attrs={"class": "fr-input"},
            )
            _DynamicForm.base_fields[field_name] = forms.EmailField(**field_kwargs)
        elif field_type == "number":
            field_kwargs["min_value"] = field.get("min")
            field_kwargs["max_value"] = field.get("max")
            field_kwargs["widget"] = forms.NumberInput(
                attrs={"class": "fr-input"},
            )
            _DynamicForm.base_fields[field_name] = forms.IntegerField(**field_kwargs)
        elif field_type == "boolean":
            _DynamicForm.base_fields[field_name] = forms.BooleanField(**field_kwargs)
        elif field_type == "choice":
            field_kwargs["choices"] = (
                (choice["name"], choice["label"]) for choice in field["choices"]
            )
            field_kwargs["widget"] = forms.widgets.Select(
                attrs={"class": "fr-select"},
            )
            _DynamicForm.base_fields[field_name] = forms.ChoiceField(**field_kwargs)
        elif field_type == "table":

            class TableauFormSet(forms.BaseFormSet):
                def add_fields(self, form, index):
                    super().add_fields(form, index)
                    for column in field["columns"]:
                        label = column["label"]
                        name = column["name"]
                        if column["type"] == "text":
                            form.fields[name] = forms.CharField(
                                label=label,
                                widget=forms.TextInput(
                                    attrs={"class": "fr-input"},
                                ),
                                required=False,
                            )
                        elif column["type"] == "number":
                            form.fields[name] = forms.IntegerField(
                                label=label,
                                widget=forms.NumberInput(
                                    attrs={"class": "fr-input"},
                                ),
                                required=False,
                            )
                        else:
                            raise Exception("Typo")

            FormSet = forms.formset_factory(
                _DynamicForm, formset=TableauFormSet, extra=1
            )
            FormSet.indicator_type = "table"
            return FormSet
        # et on continue ...

    return _DynamicForm
