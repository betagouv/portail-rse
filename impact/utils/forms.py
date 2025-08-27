from django import forms


class DsfrForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reinitialise_widgets()

    def reinitialise_widgets(self):
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.widgets.Select):
                fr_name = "fr-select"
            else:
                fr_name = "fr-input"
            field.widget.attrs.update({"class": f"{fr_name}"})
            if name in self.errors:
                field.widget.attrs.update(
                    {
                        "class": f"{fr_name} {fr_name}-error",
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
