from django.core.exceptions import ObjectDoesNotExist
from openpyxl.cell import Cell
from openpyxl.utils.cell import column_index_from_string
from openpyxl.utils.cell import coordinate_from_string

from utils.categories_juridiques import CATEGORIES_JURIDIQUES_NIVEAU_II
from utils.codes_nace import CODES_NACE
from utils.pays import CODES_PAYS_ISO_3166_1
from vsme.models import ajoute_donnes_calculees
from vsme.models import EXIGENCES_DE_PUBLICATION


def export_exigence_de_publication(exigence_de_publication, workbook, rapport_vsme):
    SCHEMA_ID_VERS_CELLULE = {
        "B1-24-a": "A4",
        "B1-24-b": "B4",
        "B1-24-c": "C4",
        "B1-24-d": "D4",
        "B1-24-e-i": "I4",
        "B1-24-e-ii": "K4",
        "B1-24-e-iii": "L4",
        "B1-24-e-iv": "M4",
        "B1-24-e-v": "N4",
        "B1-24-e-vi": "P4",
        "B1-24-e-vii": "Q4",
        "B1-25": "X4",
        "B2-26-p1": "A4",
        "B2-26-p2": "B4",
        "B2-26-p3": "C4",
        "B2-26": "E5",
        "B4-32-p1": "A4",
        "B4-32-p2": "D4",
        "B4-32-p3": "G4",
        "B6-35": "A4",
        "B6-36": "C4",
        "B7-37": "A4",
        "B7-38-ab": "B4",
        "B7-38-c": "H4",
        "B8-39-a": "A4",
        "B8-39-b": "C4",
        "B8-39-c": "G4",
        "B8-40": "I4",
        "B9-41a": "A4",
        "B9-41b": "C4",
        "B10-42-a": "A4",
        "B10-42-b": "B4",
        "B10-42-c": "E4",
        "B10-42-d": "H4",
        "B11-43-p1": "A4",
        "B11-43-p2": "B4",
    }

    for indicateur_schema_id in rapport_vsme.indicateurs_applicables(
        exigence_de_publication
    ):
        if indicateur_schema_id in SCHEMA_ID_VERS_CELLULE:
            try:
                indicateur = rapport_vsme.indicateurs.get(
                    schema_id=indicateur_schema_id
                )
            except ObjectDoesNotExist:
                continue
            worksheet = workbook[exigence_de_publication.code]
            _export_indicateur(
                indicateur,
                rapport_vsme,
                worksheet,
                SCHEMA_ID_VERS_CELLULE[indicateur_schema_id],
            )


def _export_indicateur(
    indicateur, rapport_vsme, worksheet, adresse_cellule_depart: str
):
    colonne_depart, ligne_depart = coordinate_from_string(adresse_cellule_depart)
    index_colonne_depart = column_index_from_string(colonne_depart)
    prochaine_cellule_destination = worksheet.cell(
        row=ligne_depart, column=index_colonne_depart
    )
    ajoute_donnes_calculees(indicateur.schema_id, rapport_vsme, indicateur.data)
    for champ in indicateur.schema["champs"]:
        data = indicateur.data.get(champ.get("id"))
        prochaine_cellule_destination = _export_champ(
            champ, data, prochaine_cellule_destination
        )


def _export_champ(champ, data, cellule_destination: Cell) -> Cell:
    type_indicateur = champ["type"]
    match type_indicateur:
        case "choix_multiple":
            prochaine_cellule_destination = _export_choix_multiple(
                champ, data, cellule_destination
            )
        case "tableau":
            prochaine_cellule_destination = _export_tableau(
                champ, data, cellule_destination
            )
        case "tableau_lignes_fixes":
            prochaine_cellule_destination = _export_tableau_lignes_fixes(
                champ, data, cellule_destination
            )
        case _:
            prochaine_cellule_destination = _export_simple(
                champ, data, cellule_destination
            )
    return prochaine_cellule_destination


def _export_simple(champ, data, cellule_destination: Cell) -> Cell:
    cellule_destination.value = formate_valeur(data, champ)
    prochaine_cellule_destination = cellule_destination.offset(column=1)
    return prochaine_cellule_destination


def _export_choix_multiple(champ, data, cellule_depart: Cell) -> Cell:
    for offset_ligne, valeur in enumerate(data):
        cellule_depart.offset(row=offset_ligne).value = formate_valeur(valeur, champ)
    prochaine_cellule_destination = cellule_depart.offset(column=1)
    return prochaine_cellule_destination


def formate_valeur(valeur, champ):
    match champ["type"]:
        case "choix_binaire" | "choix_binaire_radio":
            return "OUI" if valeur else "NON"
        case "choix_unique" | "choix_multiple":
            match champ["choix"]:
                case "CHOIX_FORME_JURIDIQUE":
                    return CATEGORIES_JURIDIQUES_NIVEAU_II[valeur]
                case "CHOIX_EXIGENCE_DE_PUBLICATION":
                    nom = EXIGENCES_DE_PUBLICATION[valeur].nom
                    return f"{valeur} - {nom}"
                case "CHOIX_NACE":
                    return CODES_NACE[valeur]
                case "CHOIX_PAYS":
                    return CODES_PAYS_ISO_3166_1[valeur]
                case _:  # récupération du label correspondant au choix enregistré
                    for choix in champ["choix"]:
                        if choix["id"] == valeur:
                            return choix["label"]
    return valeur


def _export_tableau(champ, data, cellule_depart: Cell) -> Cell:
    colonnes = champ["colonnes"]
    colonnes_ids = [colonne["id"] for colonne in colonnes]
    for offset_ligne, data_ligne in enumerate(data):
        for id_colonne, data_cellule in data_ligne.items():
            offset_colonne = colonnes_ids.index(id_colonne)
            _export_champ(
                colonnes[offset_colonne],
                data_cellule,
                cellule_depart.offset(row=offset_ligne, column=offset_colonne),
            )
    prochaine_cellule_destination = cellule_depart.offset(column=len(colonnes))
    return prochaine_cellule_destination


def _export_tableau_lignes_fixes(champ, data, cellule_depart: Cell) -> Cell:
    lignes = champ["lignes"]
    colonnes = champ["colonnes"]
    match lignes:
        case "PAYS":
            # une colonne pays, une colonne nombre salariés
            for offset_ligne, (code_pays, data_pays) in enumerate(data.items()):
                cellule_depart.offset(row=offset_ligne).value = CODES_PAYS_ISO_3166_1[
                    code_pays
                ]
                cellule_depart.offset(row=offset_ligne, column=1).value = data_pays[
                    "nombre_salaries"
                ]
            prochaine_cellule_destination = cellule_depart.offset(column=2)
        case list():
            colonnes_ids = [colonne["id"] for colonne in colonnes]
            if len(colonnes_ids) == 1:
                # L'export des lignes se fait en colonnes plutôt qu'en lignes
                for id_ligne, data_ligne in data.items():
                    lignes_ids = [ligne["id"] for ligne in champ["lignes"]]
                    offset_colonne = lignes_ids.index(id_ligne)
                    _export_champ(
                        colonnes[0],
                        data_ligne[colonnes_ids[0]],
                        cellule_depart.offset(column=offset_colonne),
                    )
                prochaine_cellule_destination = cellule_depart.offset(
                    column=len(lignes)
                )
            else:
                for id_ligne, data_ligne in data.items():
                    lignes_ids = [ligne["id"] for ligne in champ["lignes"]]
                    offset_ligne = lignes_ids.index(id_ligne)
                    for id_colonne, data_cellule in data_ligne.items():
                        offset_colonne = colonnes_ids.index(id_colonne)
                        _export_champ(
                            colonnes[offset_colonne],
                            data_cellule,
                            cellule_depart.offset(
                                row=offset_ligne, column=offset_colonne
                            ),
                        )
                prochaine_cellule_destination = cellule_depart.offset(
                    column=len(colonnes)
                )
    return prochaine_cellule_destination
