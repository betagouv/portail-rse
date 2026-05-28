import copy

from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Pt

from utils.pptx import find_shape
from utils.pptx import remove_shape
from utils.pptx import remove_slide
from vsme.export_xlsx import formate_valeur as formate_valeur_xlsx
from vsme.forms import THEMATIQUES_DURABILITE
from vsme.models import ExigenceDePublication
from vsme.models import EXIGENCES_DE_PUBLICATION


def export_rapport_vsme(rapport_vsme, presentation):
    indicateurs = rapport_vsme.indicateurs.all()
    export_couverture(rapport_vsme, presentation)
    export_sommaire(rapport_vsme, presentation)
    export_indicateurs(indicateurs, presentation)
    supprime_diapos_inutiles(rapport_vsme, presentation)


def export_couverture(rapport_vsme, presentation):
    shapes = presentation.slides[0].shapes
    shape_titre = find_shape(shapes, "ZoneTexte 9")
    shape_titre.text_frame.paragraphs[0].runs[
        0
    ].text = rapport_vsme.entreprise.denomination
    shape_titre.text_frame.paragraphs[1].runs[
        0
    ].text = f"Rapport VSME {rapport_vsme.annee}"


def export_sommaire(rapport_vsme, presentation):
    if rapport_vsme.choix_module == "base":
        NUMERO_DIAPO_SOMMAIRE = 3
        shapes = presentation.slides[NUMERO_DIAPO_SOMMAIRE - 1].shapes
        for num_shape in ("22", "23", "39", "40", "47", "48", "49", "54", "55", "56"):
            shape = find_shape(
                shapes, f"Round Same-side Corner of Rectangle {num_shape}"
            )
            remove_shape(shape)


def supprime_diapos_inutiles(rapport_vsme, presentation):
    diapos_a_supprimer = selectionne_diapos_a_supprimer(rapport_vsme, presentation)
    for diapo_a_supprimer in diapos_a_supprimer:
        index_diapo = diapo_a_supprimer - 1
        remove_slide(presentation, index_diapo)


def selectionne_diapos_a_supprimer(rapport_vsme, presentation):
    diapos_a_supprimer = set()

    tous_les_indicateur_schema_ids = [
        schema_id
        for exigence in EXIGENCES_DE_PUBLICATION.values()
        for schema_id in exigence.indicateurs()
    ]

    for indicateur_schema_id in tous_les_indicateur_schema_ids:
        schema_exigence = ExigenceDePublication.par_indicateur_schema_id(
            indicateur_schema_id
        ).load_json_schema()
        schema_indicateur = schema_exigence[indicateur_schema_id]
        if rapport_vsme.indicateur_est_applicable(indicateur_schema_id)[0]:
            # supprimer les diapos non applicables
            for champ in schema_indicateur["champs"]:
                if (
                    "export_pptx" in champ
                    and "diapo_non_applicable" in champ["export_pptx"]
                ):
                    diapo_a_supprimer = champ["export_pptx"]["diapo_non_applicable"]
                    diapos_a_supprimer.add(diapo_a_supprimer)
        else:
            # supprimer les diapos applicables
            for champ in schema_indicateur["champs"]:
                if (
                    "export_pptx" in champ
                    and "diapo_non_applicable" in champ["export_pptx"]
                ):
                    diapo_a_supprimer = champ["export_pptx"]["diapo"]
                    diapos_a_supprimer.add(diapo_a_supprimer)

    return sorted(diapos_a_supprimer, reverse=True)


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
    paragraphs = shape.text_frame.paragraphs
    paragraphe_a_remplir = None
    for paragraphe in shape.text_frame.paragraphs:
        if paragraphe.runs:
            paragraphe_a_remplir = paragraphe
    paragraphe_a_remplir.runs[0].text = str(valeur)


def _export_choix_multiple(champ, data, shape):
    valeurs = (formate_valeur(valeur, champ) for valeur in data)
    shape.text_frame.paragraphs[1].runs[0].text = ", ".join(valeurs)


def formate_valeur(valeur, champ):
    match champ["type"]:
        case "nombre_entier" | "nombre_decimal" | "auto_id":
            return str(valeur) if valeur else "0"
        case _:
            return str(formate_valeur_xlsx(valeur, champ))


def _export_tableau(champ, data, shape):
    table = shape.table

    nombre_lignes_a_garder = 2  # titre et première ligne de données
    trs_a_supprimer = [
        table.rows[i]._tr for i in range(nombre_lignes_a_garder, len(table.rows))
    ]
    for tr in trs_a_supprimer:
        table._tbl.remove(tr)

    nombre_lignes_a_ajouter = len(data) - 1  # première ligne déjà présente donc -1
    for _ in range(nombre_lignes_a_ajouter):
        _ajouter_ligne_tableau(table)

    for index_ligne, ligne in enumerate(data, start=1):
        for index_data, data_cellule in enumerate(ligne.values()):
            schema_colonne = champ["colonnes"][index_data]
            cell = table.cell(index_ligne, index_data)
            cell.text = formate_valeur(data_cellule, schema_colonne)
            _appliquer_style_cellule(cell, data_cellule, schema_colonne)


def _ajouter_ligne_tableau(table):
    tr_source = table.rows[1]._tr
    tr_nouveau = copy.deepcopy(tr_source)
    ns = "http://schemas.openxmlformats.org/drawingml/2006/main"
    for t in tr_nouveau.findall(f".//{{{ns}}}t"):
        t.text = ""
    table._tbl.append(tr_nouveau)


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
                    champ = colonnes[offset_colonne]
                    index_ligne = offset_ligne + 1
                    index_colonne = offset_colonne + 1
                    cell = shape.table.cell(index_ligne, index_colonne)
                    cell.text = formate_valeur(data_cellule, champ)
                    _appliquer_style_cellule(cell, data_cellule, champ)


def _appliquer_style_cellule(cell, data_cellule, champ):
    type_indicateur = champ["type"]
    for para in cell.text_frame.paragraphs:
        para.font.size = Pt(10)
        para.alignment = PP_ALIGN.CENTER
        if type_indicateur == "choix_binaire_radio":
            ROUGE = RGBColor(192, 0, 0)
            VERT = RGBColor(20, 92, 48)
            if data_cellule:
                para.font.color.rgb = VERT
            else:
                para.font.color.rgb = ROUGE
