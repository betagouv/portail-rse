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


class IndicateurForm(DsfrForm):
    pertinent = forms.BooleanField()
    indicateur_id = forms.IntegerField()


def cree_formulaire_nombre(indicateur, posted_data, index):
    if posted_data and int(posted_data["indicateur_id"][0]) == index:
        form = IndicateurForm(data=posted_data)
        initial_value = posted_data[clef][0]
    else:
        initial = {"indicateur_id": index}
        form = IndicateurForm(initial=initial)
        initial_value = None

    label = indicateur["label"]
    clef = indicateur["clef"]
    form.fields[clef] = forms.IntegerField(
        label=label,
        widget=forms.NumberInput(attrs={"class": "fr-input"}),
        initial=initial_value,
    )
    return form


def cree_formulaire_liste(indicateur, posted_data, index):
    if posted_data and int(posted_data["indicateur_id"][0]) == index:
        form = IndicateurForm(data=posted_data)
    else:
        initial = {"indicateur_id": index}
        form = IndicateurForm(initial=initial)

    for contenu in indicateur["contient"]:
        label = contenu["label"]
        clef = contenu["clef"]
        if posted_data and int(posted_data["indicateur_id"][0]) == index:
            initial_value = posted_data[clef][0]
        else:
            initial_value = None

        if contenu["type"] == "texte":
            form.fields[clef] = forms.CharField(
                label=label,
                widget=forms.TextInput(
                    attrs={"class": "fr-input"},
                ),
                initial=initial_value,
            )
        else:
            form.fields[clef] = forms.IntegerField(
                label=label,
                widget=forms.NumberInput(attrs={"class": "fr-input"}),
                initial=initial_value,
            )
    return form
