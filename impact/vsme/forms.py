from django import forms

from utils.forms import DsfrForm


EXIGENCES_DE_PUBLICATION = [
    "indicateur_nombre",
    "indicateur_nombre",
]


def forms_par_exigence_de_publication(posted_data):
    _forms = []

    class FormTableau(DsfrForm):
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
        nombre = forms.IntegerField()

        # def __init__(self, indicateur, fetched_posted_data=None, *args, **kwargs):
        #    if fetched_posted_data:
        #        if "initial" not in kwargs:
        #            kwargs["initial"] = {"indicateur_id": 23}
        #        kwargs["initial"].update(fetched_posted_data)
        #    super().__init__(*args, instance=indicateur, **kwargs)

    for index, type_indicateur in enumerate(EXIGENCES_DE_PUBLICATION, start=1):
        # fk_indicateur = vsme._meta.get_field(field_name)
        # indicateur = fk_indicateur.related_model
        # type_indicateur = indicateur.type
        if type_indicateur == "indicateur_nombre":
            if posted_data and int(posted_data["indicateur_id"][0]) == index:
                form = FormNombre(data=posted_data)
            else:
                initial = {"indicateur_id": index}
                form = FormNombre(initial=initial)
            # forms.modelform_factory(
            #    indicateur,
            #    form=FormNombre,
            #    exclude=[],
            # )
        elif type_indicateur == "indicateur_tableau":
            form = FormTableau(initial={"indicateur_id": index})
            # forms.modelform_factory(
            #    indicateur,
            #    form=FormTableau,
            #    exclude=[],
            # )
        # form.fields[field_name].value = indicateur.id
        # form.indicateur_id.value = 666 #indicateur.id
        _forms.append(form)
    return _forms
