from vsme.export_xlsx import formate_valeur


def export_pptx_exigence_de_publication(
    exigence_de_publication, presentation, indicateurs_par_schema_id
):
    for schema_id, indicateur in indicateurs_par_schema_id.items():
        _export_indicateur(indicateur, presentation)


def _export_indicateur(indicateur, presentation):
    for champ in indicateur.schema["champs"]:
        if "export_pptx" in champ:
            data = indicateur.data.get(champ["id"])
            export_pptx = champ["export_pptx"]
            numero_diapo = export_pptx["diapo"]
            diapo = presentation.slides[
                numero_diapo - 1
            ]  # décalage: slide 5 est à l'index 4
            nom_shape = export_pptx["shape"]
            for shape in diapo.shapes:
                if shape.name == nom_shape:
                    _export_champ(champ, data, shape)


def _export_champ(champ, data, shape):
    valeur = formate_valeur(data, champ)
    shape.text_frame.paragraphs[1].runs[0].text = str(valeur)
