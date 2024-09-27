from django import forms

from reglementations.models.csrd import RapportCSRD


class EnjeuxMultipleWidget(forms.CheckboxSelectMultiple):
    option_template_name = "widgets/enjeu_option.html"


class EnjeuxRapportCSRDForm(forms.ModelForm):
    enjeux = forms.ModelMultipleChoiceField(
        queryset=None, widget=EnjeuxMultipleWidget(), required=False
    )

    class Meta:
        model = RapportCSRD
        fields = ["enjeux"]

    def __init__(self, *args, esrs: str = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.esrs = esrs

        if self.instance:
            qs = self.instance.enjeux.prefetch_related("enfants")
            qs = qs.filter(esrs=self.esrs) if esrs else qs.none()

            self.fields["enjeux"].queryset = qs
            self.initial = {"enjeux": qs.filter(selection=True)}

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        for enjeu in self.instance.enjeux.filter(esrs=self.esrs):
            enjeu.selection = enjeu in self.cleaned_data["enjeux"]
            enjeu.save()

    def sections(self):
        # pas forcément optimal, mais plus simple qu'un renderer custom
        ol_starts, ol_ends, parents = [], [], []
        for idx, e in enumerate(self.fields["enjeux"].queryset):
            if e.parent_id and e.parent_id not in parents:
                # ouverture
                parents.append(e.parent_id)
                ol_starts.append(idx)
            if parents and e.parent_id != parents[-1]:
                # fermeture
                ol_ends.append(idx)
                del parents[-1]

        return (ol_starts, ol_ends)
