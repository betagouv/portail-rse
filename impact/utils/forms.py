from django import forms


class DsfrForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if type(field.widget) == forms.widgets.Select:
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
