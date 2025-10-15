import filetype
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.forms import FileField
from django.forms.widgets import RadioSelect

from analyseia.models import AnalyseIA
from reglementations.models.csrd import Enjeu
from reglementations.models.csrd import RapportCSRD


MAX_UPLOAD_SIZE = 50 * 1024 * 1024


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
            qs = self.instance.enjeux_par_esrs(self.esrs)
            self.fields["enjeux"].queryset = qs
            self.initial = {"enjeux": qs.selectionnes()}

    def save(self, *args, **kwargs):
        if self.instance.bloque:
            return

        super().save(*args, **kwargs)

        for enjeu in self.instance.enjeux.filter(esrs=self.esrs):
            enjeu.selection = enjeu in self.cleaned_data["enjeux"]
            if not enjeu.selection:
                # si un enjeu n'est pas sélectionné, il ne peut pas être analysé
                # (raz éventuelle de l'analyse si on déselectionne l'enjeu)
                enjeu.materiel = None
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


class EnjeuxMaterielsRapportCSRDForm(forms.Form):
    """
    Formulaire permettant de modifier la matérialité des enjeux :
     - pas de ModelForm : il est beaucoup plus facile de travailler directement sur un queryset,
     - pas de widget custom : les radios sont directement affichés dans le gabarit (et l'implémentation de la widget s'avérait difficile à lire).
    """

    def __init__(self, *args, qs=None, **kwargs):
        super().__init__(*args, **kwargs)
        if qs:
            self.qs = qs
            for enjeu in qs:
                self.fields[f"enjeu_{enjeu.pk}"] = forms.NullBooleanField(
                    label=enjeu.nom,
                    help_text="enjeu personnel" if enjeu.modifiable else None,
                    required=False,
                    initial=enjeu.materiel,
                    widget=RadioSelect(
                        choices=[(True, "Matériel"), (False, "Non-matériel")]
                    ),
                )

    def save(self):
        for enjeu in self.qs:
            enjeu.materiel = self.cleaned_data[f"enjeu_{enjeu.pk}"]
            enjeu.save()


class LienRapportCSRDForm(forms.ModelForm):
    lien_rapport = forms.URLField()

    class Meta:
        model = RapportCSRD
        fields = ["lien_rapport"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["lien_rapport"].widget.attrs.update(
            {"class": "fr-input", "placeholder": "URL du rapport CSRD"}
        )

    def clean(self):
        if self.cleaned_data.get("lien_rapport"):
            self.instance.bloque = True

        return self.cleaned_data


def validate_pdf_content(value):
    kind = filetype.guess(value)
    if (not kind) or kind.extension != "pdf":
        raise ValidationError(
            "Le fichier %(value)s n'est pas un pdf.",
            params={"value": value},
        )


def validate_file_size(value):
    if value.size > MAX_UPLOAD_SIZE:
        raise ValidationError(
            "La taille du fichier dépasse la taille maximale autorisée"
        )


class DocumentAnalyseIAForm(forms.ModelForm):
    fichier = FileField(
        validators=[
            FileExtensionValidator(["pdf"]),
            validate_pdf_content,
            validate_file_size,
        ],
        help_text="Sélectionnez des documents contenant des <b>données publiques</b> susceptibles de répondre à vos exigences ESRS.<br>Taille maximale : <b>50 Mo</b>. Format supporté : <b>PDF</b>. Langue du document : <b>Français</b>.",
    )

    class Meta:
        model = AnalyseIA
        fields = ["fichier"]
        labels = {"fichier": "Ajouter un fichier"}
