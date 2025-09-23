from django import forms

from utils.categories_juridiques import CATEGORIES_JURIDIQUES_NIVEAU_II
from utils.codes_nace import CODES_NACE
from utils.forms import DsfrForm
from utils.forms import DsfrFormSet
from utils.pays import CODES_PAYS_ISO_3166_1
from vsme.models import EXIGENCES_DE_PUBLICATION

NON_PERTINENT_FIELD_NAME = "non_pertinent"


def create_multiform_from_schema(schema, **kwargs):
    class _MultiForm:
        Forms = []
        si_pertinent = schema.get("si_pertinent", False)

        def __init__(self, *args, **kwargs):
            self.forms = []
            for Form in self.Forms:
                self.forms.append(Form(*args, **kwargs))
            if self.si_pertinent:
                # désactive tous les champs du multiform (sauf le champ non pertinent)
                # lorsque le multiform est initialisé avec une valeur positive du champ non pertinent.
                # Si le multiform est initialisé à la fois avec les données d'un dictionnaire initial
                # et celles d'un dictionnaire data (postées par l'utilisateur)
                # c'est les données postées qui prévalent
                self.non_pertinent = None
                if kwargs and kwargs.get("initial"):
                    self.non_pertinent = kwargs["initial"].get(NON_PERTINENT_FIELD_NAME)
                if args:
                    data = args[0]
                    self.non_pertinent = data.get(NON_PERTINENT_FIELD_NAME)
                if self.non_pertinent:
                    self.disable_fields()

        @classmethod
        def add_Form(cls, Form):
            cls.Forms.append(Form)

        def is_valid(self):
            self.clean()
            return all([form.is_valid() for form in self.forms])

        def clean(self):
            if self.si_pertinent and not self.non_pertinent:
                for form in self.forms:
                    if isinstance(form, forms.Form):
                        for field in form.fields:
                            if (
                                field != NON_PERTINENT_FIELD_NAME
                                and not form.cleaned_data.get(field)
                            ):
                                form.add_error(
                                    field,
                                    "Ce champ est requis lorsque l'indicateur est déclaré comme pertinent",
                                )

        @property
        def cleaned_data(self):
            cleaned_data = {}
            for form in self.forms:
                cleaned_data.update(form.cleaned_data)
            return cleaned_data

        def disable_fields(self):
            for form in self.forms:
                if isinstance(form, forms.Form):
                    for field in form.fields:
                        if field != NON_PERTINENT_FIELD_NAME:
                            form.fields[field].disabled = True
                else:  # FormSet
                    form.min_num = 0
                    form.validate_min = False
                    for form_table in form.forms:
                        for field in form_table.fields:
                            form_table.fields[field].disabled = True

    def _dynamicform_factory():
        class _DynamicForm(DsfrForm):
            pass

        return _DynamicForm

    _DynamicForm = _dynamicform_factory()

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
            case "text" | "number" | "boolean" | "choice" | "multiple_choice":
                _DynamicForm.base_fields[field_name] = create_simple_field_from_schema(
                    field
                )
            case "table":
                if _DynamicForm.base_fields:
                    _MultiForm.add_Form(_DynamicForm)
                    _DynamicForm = _dynamicform_factory()

                class TableauFormSet(DsfrFormSet):
                    name = field["name"]
                    columns = field["columns"]

                    def __init__(self, *args, **kwargs):
                        if kwargs.get("initial"):
                            formset_initial = kwargs["initial"].get(self.name)
                            kwargs["initial"] = formset_initial
                        super().__init__(*args, **kwargs)

                    def add_fields(self, form, index):
                        super().add_fields(form, index)
                        for column in self.columns:
                            field_name = column["name"]
                            form.fields[field_name] = create_simple_field_from_schema(
                                column
                            )

                    @property
                    def cleaned_data(self):
                        super().cleaned_data
                        # surcharge cleaned_data pour supprimer les valeurs des lignes supprimées
                        # et retourner un dictionnaire comme un formulaire standard
                        return {
                            self.name: [
                                form.cleaned_data
                                for form in self.forms
                                if form not in self.deleted_forms
                            ]
                        }

                extra = kwargs.get("extra", 0)
                min_num = 1 if _MultiForm.si_pertinent else None
                FormSet = forms.formset_factory(
                    DsfrForm,
                    formset=TableauFormSet,
                    extra=extra,
                    can_delete=True,
                    min_num=min_num,
                    validate_min=bool(min_num),
                )
                FormSet.indicator_type = "table"
                _MultiForm.add_Form(FormSet)

    if _DynamicForm.base_fields:
        _MultiForm.add_Form(_DynamicForm)

    return _MultiForm


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
        case "choice" | "multiple_choice" as field_type:
            match field_schema["choices"]:
                case "CHOIX_PAYS":
                    choices = CODES_PAYS_ISO_3166_1
                case "CHOIX_FORME_JURIDIQUE":
                    choices = CATEGORIES_JURIDIQUES_NIVEAU_II
                case "CHOIX_NACE":
                    choices = [
                        (code, f"{code} - {nom}") for code, nom in CODES_NACE.items()
                    ]
                case "CHOIX_EXIGENCE_DE_PUBLICATION":
                    choices = [
                        (
                            exigence_de_publication.code,
                            f"{exigence_de_publication.code} - {exigence_de_publication.nom}",
                        )
                        for exigence_de_publication in EXIGENCES_DE_PUBLICATION.values()
                    ]
                case _:
                    choices = (
                        (choice["name"], choice["label"])
                        for choice in field_schema["choices"]
                    )
            if field_type == "choice":
                return forms.ChoiceField(choices=choices, **field_kwargs)
            else:
                return forms.MultipleChoiceField(
                    widget=forms.CheckboxSelectMultiple,
                    choices=choices,
                    **field_kwargs,
                )
        case _:
            raise Exception(f"Type inconnu : {field_type}")
