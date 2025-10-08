from django import forms


class DsfrForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reinitialise_widgets()

    def reinitialise_widgets(self):
        for name, field in self.fields.items():
            match field.widget:
                case forms.widgets.Select():
                    dsfr_class_name = "fr-select"
                case forms.widgets.CheckboxSelectMultiple() | forms.RadioSelect():
                    dsfr_class_name = None
                case _:
                    dsfr_class_name = "fr-input"
            if dsfr_class_name:
                field.widget.attrs.update({"class": f"{dsfr_class_name}"})
            if name in self.errors and dsfr_class_name:
                field.widget.attrs.update(
                    {
                        "class": f"{dsfr_class_name} {dsfr_class_name}-error",
                        "aria-describedby": f"{name}-error-desc-error",
                    }
                )


class DsfrFormSet(forms.BaseFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for form in self.forms:
            form.reinitialise_widgets()


class DateInput(forms.DateInput):
    input_type = "date"
