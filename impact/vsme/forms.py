import re
from json.decoder import JSONDecodeError

import geojson
from django import forms
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from django.utils.html import format_html_join
from django.utils.safestring import mark_safe

from utils.categories_juridiques import CATEGORIES_JURIDIQUES_NIVEAU_II
from utils.codes_nace import CODES_NACE
from utils.forms import DsfrForm
from utils.forms import DsfrFormSet
from utils.pays import CODES_PAYS_ISO_3166_1
from vsme.models import EXIGENCES_DE_PUBLICATION

NON_PERTINENT_FIELD_NAME = "non_pertinent"


def create_multiform_from_schema(
    schema, toggle_pertinent_url, extra=0, infos_preremplissage=None
):
    class _MultiForm:
        Forms = []
        si_pertinent = schema.get("si_pertinent", False)
        preremplissage = infos_preremplissage

        def __init__(self, *args, **kwargs):
            if self.preremplissage:
                kwargs["initial"] = self.preremplissage["initial"]
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
                                and not form.cleaned_data.get(field) == 0
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

    if si_pertinent := schema.get("si_pertinent", False):
        _DynamicForm.base_fields[NON_PERTINENT_FIELD_NAME] = forms.BooleanField(
            label=si_pertinent if type(si_pertinent) == str else "Non pertinent",
            required=False,
            widget=forms.BooleanField.widget(attrs={"hx-post": toggle_pertinent_url}),
        )
    fields = schema["champs"]
    for field in fields:
        field_name = field["id"]
        field_type = field["type"]

        match field_type:
            case (
                "texte"
                | "texte_long"
                | "nombre_entier"
                | "nombre_decimal"
                | "date"
                | "choix_binaire"
                | "choix_unique"
                | "choix_multiple"
                | "auto_id"
            ):
                _DynamicForm.base_fields[field_name] = create_simple_field_from_schema(
                    field
                )
            case "tableau" | "tableau_lignes_fixes":
                if _DynamicForm.base_fields:
                    _MultiForm.add_Form(_DynamicForm)
                    _DynamicForm = _dynamicform_factory()

                FormSet = create_Formset_from_schema(field, extra)

                _MultiForm.add_Form(FormSet)

    if _DynamicForm.base_fields:
        _MultiForm.add_Form(_DynamicForm)

    return _MultiForm


def create_simple_field_from_schema(field_schema):
    field_name = field_schema["id"]
    field_type = field_schema["type"]
    field_kwargs = {
        "label": field_schema.get("label", field_name),
        "required": field_schema.get("obligatoire", False),
        # ...
    }
    if description := field_schema.get("description"):
        field_kwargs["help_text"] = description
    match field_type:
        case "auto_id":
            field = forms.IntegerField(min_value=1, required=True)
            field.auto_id = True
            return field
        case "texte":
            field_kwargs["max_length"] = field_schema.get("max_length", 255)
            if suggestions := field_schema.get("suggestions"):
                widget = DatalistTextInput(options=suggestions)
            else:
                widget = None
            return forms.CharField(
                widget=widget,
                **field_kwargs,
            )
        case "texte_long":
            return forms.CharField(
                widget=forms.Textarea(),
                **field_kwargs,
            )
        case "nombre_entier" | "auto_id":
            field_kwargs["min_value"] = field_schema.get("min")
            field_kwargs["max_value"] = field_schema.get("max")
            return forms.IntegerField(**field_kwargs)
        case "nombre_decimal":
            return forms.FloatField(**field_kwargs)
        case "date":
            return forms.DateField(
                widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
                **field_kwargs,
            )
        case "choix_binaire":
            return forms.BooleanField(**field_kwargs)
        case "choix_binaire_radio":
            return forms.BooleanField(
                widget=forms.RadioSelect(choices=[(True, "Oui"), (False, "Non")]),
                **field_kwargs,
            )
        case "choix_unique" | "choix_multiple":
            match field_schema["choix"]:
                case "CHOIX_PAYS":
                    choices = CODES_PAYS_ISO_3166_1
                    field_kwargs["initial"] = ("FRA", "FRANCE")
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
                        (choice["id"], choice["label"])
                        for choice in field_schema["choix"]
                    )
            if field_type == "choix_unique":
                return forms.ChoiceField(choices=choices, **field_kwargs)
            else:  # choix_multiple
                return forms.MultipleChoiceField(
                    widget=forms.CheckboxSelectMultiple,
                    choices=choices,
                    **field_kwargs,
                )
        case "geolocalisation":
            return GeoField(**field_kwargs)
        case _:
            raise Exception(f"Type inconnu : {field_type}")


class GeoField(forms.CharField):
    geolocalisation = True

    def clean(self, value):
        cleaned_value = super().clean(value)
        minimized_cleaned_value = re.sub(
            r"\s+", "", cleaned_value
        )  # supprime tous les caractères d'espacement
        if not minimized_cleaned_value.startswith("["):
            minimized_cleaned_value = f"[{minimized_cleaned_value}]"
        try:
            coordonnees = geojson.loads(minimized_cleaned_value)
        except JSONDecodeError:
            raise ValidationError("Les coordonnées sont incorrectes")
        point = geojson.Point(coordonnees)
        polygon = geojson.Polygon(coordonnees)
        if not point.is_valid and not polygon.is_valid:
            raise ValidationError("Les coordonnées sont incorrectes")
        return minimized_cleaned_value


class DatalistTextInput(forms.TextInput):
    def __init__(self, options, attrs=None):
        super().__init__(attrs)
        self.options = options

    def render(self, name, value, attrs=None, renderer=None):
        self.datalist_id = f"datalist_{name}"

        # Ajoute l'attribut 'list' à l'input pour le lier à la datalist
        if attrs is None:
            attrs = {}
        attrs["list"] = self.datalist_id

        # Génère l'input standard
        input_html = super().render(name, value, attrs, renderer)

        # Génère la datalist avec les options
        datalist_html = self._render_datalist()

        # Combine l'input et la datalist
        return mark_safe(f"{input_html}{datalist_html}")

    def _render_datalist(self):
        options_html = format_html_join(
            "\n",
            "<option value='{}'></option>",
            ((option,) for option in self.options),
        )

        return format_html(
            "<datalist id='{}'>{}</datalist>",
            self.datalist_id,
            options_html,
        )


def create_Formset_from_schema(field_schema, extra=0):
    field_type = field_schema["type"]

    class TableauFormSet(DsfrFormSet):
        id = field_schema["id"]
        label = field_schema["label"]
        description = field_schema.get("description")
        columns = field_schema["colonnes"]

        def add_fields(self, form, index):
            super().add_fields(form, index)
            for column in self.columns:
                field_name = column["id"]
                form.fields[field_name] = create_simple_field_from_schema(column)

    class TableauLignesLibresFormSet(TableauFormSet):
        indicator_type = "table"

        def __init__(self, *args, **kwargs):
            if kwargs.get("initial"):
                formset_initial = kwargs["initial"].get(self.id)
                kwargs["initial"] = formset_initial
            self.default_error_messages["too_few_forms"] = (
                "Le tableau doit contenir au moins une ligne."
            )
            super().__init__(*args, **kwargs)

        @property
        def cleaned_data(self):
            super().cleaned_data
            # surcharge cleaned_data pour supprimer les valeurs des lignes supprimées
            # et retourner un dictionnaire comme un formulaire standard
            cleaned_data = {self.id: []}
            for form in self.forms:
                if form not in self.deleted_forms:
                    row = [
                        {
                            field_name: field_value
                            for field_name, field_value in form.cleaned_data.items()
                            if field_name != "DELETE"
                        }
                    ]
                    cleaned_data[self.id] = cleaned_data[self.id] + row
            return cleaned_data

    class TableauLignesFixesFormSet(TableauFormSet):
        indicator_type = "table_lignes_fixes"
        rows = field_schema.get("lignes")

        def __init__(self, *args, **kwargs):
            if kwargs.get("initial"):
                formset_initial = kwargs["initial"].get(self.id)
                if formset_initial:
                    kwargs["initial"] = list(formset_initial.values())
                else:
                    kwargs["initial"] = [{} for row in self.rows]
            else:
                kwargs["initial"] = [{} for row in self.rows]
            super().__init__(*args, **kwargs)

        @property
        def cleaned_data(self):
            super().cleaned_data
            # surcharge cleaned_data pour retourner un dictionnaire de dictionnaires
            # chaque ligne est représentée par un dictionnaire
            # par exemple :
            # {
            #   declaration_durabilite: {
            #       changement_climatique: {pratiques: True, accessibles: True},
            #       pollution: {pratiques: True, accessibles: True, cibles: True},
            #       ...
            # }
            cleaned_data = {self.id: {row["id"]: {} for row in self.rows}}
            for index, form in enumerate(self.forms):
                cleaned_data[self.id][self.rows[index]["id"]] = form.cleaned_data
            return cleaned_data

    if field_type == "tableau":
        FormSet = forms.formset_factory(
            DsfrForm,
            formset=TableauLignesLibresFormSet,
            extra=extra,
            can_delete=True,
            min_num=1,
            validate_min=True,
        )
    else:  # "tableau_lignes_fixes"
        nb_lignes = len(field_schema["lignes"])
        FormSet = forms.formset_factory(
            DsfrForm,
            formset=TableauLignesFixesFormSet,
            extra=0,
            min_num=nb_lignes,
            max_num=nb_lignes,
            validate_min=True,
            validate_max=True,
        )

    return FormSet
