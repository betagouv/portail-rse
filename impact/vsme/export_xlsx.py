from openpyxl.cell import Cell
from openpyxl.utils.cell import column_index_from_string
from openpyxl.utils.cell import coordinate_from_string

from utils.categories_juridiques import CATEGORIES_JURIDIQUES_NIVEAU_II
from utils.codes_nace import CODES_NACE
from utils.pays import CODES_PAYS_ISO_3166_1
from vsme.forms import THEMATIQUES_DURABILITE
from vsme.models import EXIGENCES_DE_PUBLICATION


def export_exigence_de_publication(
    exigence_de_publication, workbook, indicateurs_par_schema_id
):
    schema_ids = exigence_de_publication.indicateurs()
    for indicateur_schema_id in schema_ids:
        try:
            indicateur = indicateurs_par_schema_id[indicateur_schema_id]
        except KeyError:
            continue
        worksheet = workbook[exigence_de_publication.code]
        _export_indicateur(
            indicateur,
            worksheet,
        )


def _export_indicateur(indicateur, worksheet):
    adresse_cellule_depart = indicateur.schema["export_xlsx"]["cellule"]
    if indicateur.est_non_pertinent:
        return
    indicateur_data = indicateur.data
    colonne_depart, ligne_depart = coordinate_from_string(adresse_cellule_depart)
    index_colonne_depart = column_index_from_string(colonne_depart)
    prochaine_cellule_destination = worksheet.cell(
        row=ligne_depart, column=index_colonne_depart
    )
    for champ in indicateur.schema["champs"]:
        champ_data = indicateur_data.get(champ.get("id"))
        prochaine_cellule_destination = _export_champ(
            champ, champ_data, prochaine_cellule_destination
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
                case "CHOIX_SITES":
                    return valeur  # id du site
                case "CHOIX_COMBUSTIBLE":
                    return valeur
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
    match champ["id"]:
        # hack car l'export excel de ces indicateurs qui contiennent des tableaux lignes fixes est trop complexe
        # à cause du décalage produit par les premières colonnes contenant les labels des lignes écrits en dur dans le template
        # TODO: il faudrait plutôt coder l'export des labels de lignes plutôt que laisser cette responsabilité au template
        case "cibles_reduction_emissions_GES_scopes_1_2":
            # cell.parent permet de récupérer le worksheet
            cellule_depart = cellule_depart.parent["D4"]
        case "total_reduction_emissions_GES_scopes_1_2":
            cellule_depart = cellule_depart.parent["D6"]
        case "total_reduction_emissions_GES_scope_3":
            cellule_depart = cellule_depart.parent["I19"]
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
        case "RISQUES_CLIMATIQUES":
            for offset_ligne, (id_risque, data_risque) in enumerate(data.items()):
                for offset_colonne, colonne in enumerate(colonnes):
                    _export_champ(
                        colonne,
                        data_risque[colonne["id"]],
                        cellule_depart.offset(row=offset_ligne, column=offset_colonne),
                    )
            prochaine_cellule_destination = cellule_depart.offset(column=len(colonnes))
        case "THEMATIQUES_DURABILITE" | list():
            colonnes_ids = [colonne["id"] for colonne in colonnes]
            if lignes == "THEMATIQUES_DURABILITE":
                lignes_ids = list(THEMATIQUES_DURABILITE.keys())
            else:
                lignes_ids = [ligne["id"] for ligne in lignes]
            if len(colonnes_ids) == 1:
                # L'export des lignes se fait en colonnes plutôt qu'en lignes
                for id_ligne, data_ligne in data.items():
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
