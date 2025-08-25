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


def create_form_from_yaml(yaml_data):
    class _DynamicForm(forms.Form):
        pass

    for field in yaml_data["fields"]:
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
            _DynamicForm.base_fields[field_name] = forms.CharField(**field_kwargs)
        elif field_type == "email":
            _DynamicForm.base_fields[field_name] = forms.EmailField(**field_kwargs)
        elif field_type == "number":
            field_kwargs["min_value"] = field.get("min")
            field_kwargs["max_value"] = field.get("max")
            _DynamicForm.base_fields[field_name] = forms.IntegerField(**field_kwargs)
        elif field_type == "boolean":
            _DynamicForm.base_fields[field_name] = forms.BooleanField(**field_kwargs)
        # et on continue ...

    return _DynamicForm


# Charger le schéma YAML et créer le formulaire
# yaml_data = load_yaml_schema("./defs/form_schema.yaml")
# MonFormulaireDynamique = create_form_from_yaml(yaml_data)
