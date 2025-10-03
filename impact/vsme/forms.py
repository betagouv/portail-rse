from django import forms

from utils.forms import DsfrForm
from vsme.schema import Tableau

NON_PERTINENT_FIELD_NAME = "non_pertinent"


def create_multiform_from_schema(indicateur_schema, **kwargs):
    class _MultiForm:
        Forms = []
        si_pertinent = indicateur_schema.si_pertinent

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

    if indicateur_schema.si_pertinent:
        _DynamicForm.base_fields[NON_PERTINENT_FIELD_NAME] = forms.BooleanField(
            required=False,
            widget=forms.BooleanField.widget(
                attrs={"hx-post": kwargs["toggle_pertinent_url"]}
            ),
        )

    for champ in indicateur_schema.champs:
        if isinstance(champ, Tableau):
            if _DynamicForm.base_fields:
                _MultiForm.add_Form(_DynamicForm)
                _DynamicForm = _dynamicform_factory()

            FormSet = champ.to_django_formset(extra=kwargs.get("extra", 0))
            _MultiForm.add_Form(FormSet)
        else:
            # Champ basique
            _DynamicForm.base_fields[champ.id] = champ.to_django_field()

    if _DynamicForm.base_fields:
        _MultiForm.add_Form(_DynamicForm)

    return _MultiForm
