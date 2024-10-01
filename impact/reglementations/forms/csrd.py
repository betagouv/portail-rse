from django import forms
from django.db.models import F
from django.db.models import IntegerField
from django.db.models.query import Cast

from reglementations.models.csrd import Enjeu
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
            # l'ordre d'affichage (par pk) est inversé selon que l'enjeu est modifiable ou pas
            qs = qs.annotate(
                ord=Cast("modifiable", output_field=IntegerField()) * F("pk")
            ).order_by("-ord", "pk")

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


class NouvelEnjeuCSRDForm(forms.ModelForm):
    # creation_enjeu = forms.BooleanField()
    titre = forms.CharField(widget=forms.TextInput, initial="")

    # `details` et pas `description` : le rapport CSRD étant utilisé en modèle,
    # il peut y avoir confusion avec le champ `RapportCSRD.description`
    details = forms.CharField(widget=forms.Textarea, required=False, initial="")

    class Meta:
        model = RapportCSRD
        fields = ["titre", "details"]

    def __init__(self, *args, esrs: str = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.esrs = esrs

    def clean_titre(self):
        # on vérifie juste si un titre similaire existe pour cet ESRS
        titre = self.cleaned_data["titre"]

        if Enjeu.objects.filter(
            rapport_csrd=self.instance, esrs=self.esrs, nom=titre.strip()
        ).exists():
            raise forms.ValidationError(
                "Un enjeu existe déjà avec ce titre dans cet ESRS", code="dup_titre"
            )

        return titre

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        Enjeu(
            rapport_csrd=self.instance,
            esrs=self.esrs,
            modifiable=True,
            selection=True,
            nom=self.cleaned_data["titre"],
            description=self.cleaned_data["details"].strip(),
        ).save()
