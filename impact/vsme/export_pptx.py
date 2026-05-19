from utils.pptx import find_shape
from utils.pptx import remove_shape
from vsme.export_xlsx import formate_valeur
from vsme.forms import THEMATIQUES_DURABILITE


def export_rapport_vsme(rapport_vsme, presentation):
    indicateurs = rapport_vsme.indicateurs.all()
    export_indicateurs(indicateurs, presentation)


def export_sommaire(rapport_vsme, presentation):
    if rapport_vsme.choix_module == "base":
        NUMERO_DIAPO_SOMMAIRE = 3
        shapes = presentation.slides[NUMERO_DIAPO_SOMMAIRE - 1].shapes
        shape = find_shape(shapes, "Round Same-side Corner of Rectangle 21")
        remove_shape(shape)


def export_indicateurs(indicateurs, presentation):
    for indicateur in indicateurs:
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
    type_indicateur = champ["type"]
    match type_indicateur:
        case "choix_multiple":
            _export_choix_multiple(champ, data, shape)
        case "tableau":
            _export_tableau(champ, data, shape)
        case "tableau_lignes_fixes":
            _export_tableau_lignes_fixes(champ, data, shape)
        case _:
            _export_simple(champ, data, shape)


def _export_simple(champ, data, shape):
    valeur = formate_valeur(data, champ)
    shape.text_frame.paragraphs[1].runs[0].text = str(valeur)


def _export_choix_multiple(champ, data, shape):
    valeurs = (formate_valeur(valeur, champ) for valeur in data)
    shape.text_frame.paragraphs[1].runs[0].text = ", ".join(valeurs)


def _export_tableau(champ, data, shape):
    for index_ligne, ligne in enumerate(data, start=1):
        for index_data, data in enumerate(ligne.values()):
            schema_colonne = champ["colonnes"][index_data]
            valeur = formate_valeur(data, schema_colonne)
            shape.table.cell(index_ligne, index_data).text = str(valeur)


def _export_tableau_lignes_fixes(champ, data, shape):
    lignes = champ["lignes"]
    colonnes = champ["colonnes"]
    match lignes:
        case "THEMATIQUES_DURABILITE" | list():
            colonnes_ids = [colonne["id"] for colonne in colonnes]
            if lignes == "THEMATIQUES_DURABILITE":
                lignes_ids = list(THEMATIQUES_DURABILITE.keys())
            else:
                lignes_ids = [ligne["id"] for ligne in lignes]

            for id_ligne, data_ligne in data.items():
                offset_ligne = lignes_ids.index(id_ligne)
                for id_colonne, data_cellule in data_ligne.items():
                    offset_colonne = colonnes_ids.index(id_colonne)
                    valeur = formate_valeur(data_cellule, colonnes[offset_colonne])
                    index_ligne = offset_ligne + 1
                    index_colonne = offset_colonne + 1
                    shape.table.cell(index_ligne, index_colonne).text = str(valeur)
