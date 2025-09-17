from django import forms

from utils.forms import DsfrForm
from utils.forms import DsfrFormSet
from vsme.models import EXIGENCES_DE_PUBLICATION

NON_PERTINENT_FIELD_NAME = "non_pertinent"


def create_form_from_schema(schema, **kwargs):
    class _DynamicForm(DsfrForm):
        # def __init__(self, *args, **kwargs):
        #     super().__init__(*args, **kwargs)
        #     if NON_PERTINENT_FIELD_NAME in self.fields and self.initial and self.initial.get(NON_PERTINENT_FIELD_NAME):
        #         for field in self.fields:
        #             if field != NON_PERTINENT_FIELD_NAME:
        #                 self.fields[field].disabled = True

        def clean(self):
            super().clean()

            if NON_PERTINENT_FIELD_NAME in self.fields:
                non_pertinent = self.cleaned_data.get(NON_PERTINENT_FIELD_NAME)
                if not non_pertinent:
                    for field in self.fields:
                        if (
                            field != NON_PERTINENT_FIELD_NAME
                            and not self.cleaned_data.get(field)
                        ):
                            self.add_error(
                                field,
                                "Ce champ est requis lorsque l'indicateur est déclaré comme pertinent",
                            )

    if schema.get("si_pertinent", False):
        _DynamicForm.base_fields[NON_PERTINENT_FIELD_NAME] = forms.BooleanField(
            required=False,
            widget=forms.BooleanField.widget(
                attrs={"hx-post": kwargs["toggle_pertinent_url"]}
            ),
        )

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
                    def __init__(self, *args, **kwargs):
                        self.non_pertinent = None
                        # nécessaire si on a un indicateur de type tableau non obligatoire (qui peut être non pertinent)
                        # mais fonctionne seulement si on n'a pas plusieurs champs dont 1 de type tableau dans un indicateur
                        # si c'est possible il faudrait plutôt gérer proprement le cas d'avoir plusieurs formsets/forms...
                        # et le non_pertinent serait géré plus proprement dans un form à part, sans toucher au formset ?
                        # ce cas de plusieurs champs dont 1 de type tableau n'est pas géré aujourd'hui (même sans l'histoire de pertinence)
                        self.name = field["name"]
                        if kwargs and kwargs.get("initial"):
                            self.non_pertinent = kwargs["initial"].get(
                                NON_PERTINENT_FIELD_NAME
                            )
                            formset_initial = kwargs["initial"].get(self.name)
                            kwargs["initial"] = formset_initial
                        if args:
                            data = args[0]
                            self.non_pertinent = data.get(NON_PERTINENT_FIELD_NAME)
                        super().__init__(*args, **kwargs)
                        # if self.non_pertinent:
                        #     for form in self.forms:
                        #         for field in form.fields:
                        #             form.fields[field].disabled

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
                        # et ajouter le champ non pertinent éventuel
                        cleaned_data = {}
                        if self.non_pertinent:
                            cleaned_data[NON_PERTINENT_FIELD_NAME] = bool(
                                self.non_pertinent
                            )
                        cleaned_data[self.name] = [
                            form.cleaned_data
                            for form in self.forms
                            if form not in self.deleted_forms
                        ]
                        return cleaned_data

                extra = kwargs.get("extra", 0)
                FormSet = forms.formset_factory(
                    DsfrForm, formset=TableauFormSet, extra=extra, can_delete=True
                )  # TODO: ajouter les params django min_num et validate_min pour ne pas enregistrer de valeur nulle ?
                # Le fait de ne pas utiliser DynamicForm permet de ne pas trimballer des champs non_pertinents à chaque ligne du formset
                # mais il serait peut être plus malin de ne pas ajouter de champ non_pertinent dans le DynamicForm comme on le fait actuellement
                # traiter à part ce champ non_pertinent ?
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
