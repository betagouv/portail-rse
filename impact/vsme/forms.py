from django import forms

from utils.forms import DsfrForm


EXIGENCES_DE_PUBLICATION = [
    {
        "type": "indicateur_nombre",
        "label": "Bilan net",
        "clef": "bilan",
    },
    {
        "type": "indicateur_liste",
        "contient": [
            {
                "label": "Nom de la filiale",
                "clef": "nom",
                "type": "texte",
            },
            {
                "label": "Chiffre daffaire",
                "clef": "CA",
                "type": "nombre",
            },
        ],
    },
]


def forms_par_exigence_de_publication(posted_data):
    _forms = []

    for index, indicateur in enumerate(EXIGENCES_DE_PUBLICATION, start=1):
        # fk_indicateur = vsme._meta.get_field(field_name)
        # indicateur = fk_indicateur.related_model
        type_indicateur = indicateur["type"]
        if type_indicateur == "indicateur_nombre":
            form = cree_formulaire_nombre(indicateur, posted_data, index)
        elif type_indicateur == "indicateur_liste":
            form = cree_formulaire_liste(indicateur, posted_data, index)

        _forms.append(form)
    return _forms


class FormListe(DsfrForm):
    pertinent = forms.BooleanField()
    indicateur_id = forms.IntegerField()


#    class Meta:
#        model = IndicateurTableau
#        exclude = []
#
#    def __init__(self, indicateur, fetched_posted_data=None, *args, **kwargs):
#        if fetched_posted_data:
#            if "initial" not in kwargs:
#                kwargs["initial"] = {"indicateur_id": 23}
#            kwargs["initial"].update(fetched_posted_data)
#        super().__init__(*args, instance=indicateur, **kwargs)


class FormNombre(DsfrForm):
    pertinent = forms.BooleanField()
    indicateur_id = forms.IntegerField()

    # def __init__(self, indicateur, fetched_posted_data=None, *args, **kwargs):
    #    if fetched_posted_data:
    #        if "initial" not in kwargs:
    #            kwargs["initial"] = {"indicateur_id": 23}
    #        kwargs["initial"].update(fetched_posted_data)
    #    super().__init__(*args, instance=indicateur, **kwargs)


def cree_formulaire_nombre(indicateur, posted_data, index):
    label = indicateur["label"]
    clef = indicateur["clef"]
    if posted_data and int(posted_data["indicateur_id"][0]) == index:
        form = FormNombre(data=posted_data)
        initial_value = posted_data[clef][0]
    else:
        initial = {"indicateur_id": index}
        form = FormNombre(initial=initial)
        initial_value = None
    form.fields[clef] = forms.IntegerField(
        label=label,
        widget=forms.NumberInput(attrs={"class": "fr-input"}),
        initial=initial_value,
    )
    return form
    # forms.modelform_factory(
    #    indicateur,
    #    form=FormNombre,
    #    exclude=[],
    # )


def cree_formulaire_liste(indicateur, posted_data, index):
    form = FormListe(initial={"indicateur_id": index})
    for contenu in indicateur["contient"]:
        label = contenu["label"]
        clef = contenu["clef"]
        if contenu["type"] == "texte":
            form.fields[clef] = forms.CharField(
                label=label, widget=forms.TextInput(attrs={"class": "fr-input"})
            )
        else:
            form.fields[clef] = forms.IntegerField(
                label=label,
                widget=forms.NumberInput(attrs={"class": "fr-input"}),
            )
    return form

    # forms.modelform_factory(
    #    indicateur,
    #    form=FormTableau,
    #    exclude=[],
    # )
