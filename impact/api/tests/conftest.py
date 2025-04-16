from datetime import date

import pytest

from entreprises.models import CaracteristiquesAnnuelles


INFOS_ENTREPRISE = {
    "siren": "000000001",
    "denomination": "Entreprise SAS",
    "effectif": CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
    "categorie_juridique_sirene": 5710,
    "code_pays_etranger_sirene": None,
    "code_NAF": "01.11Z",
}


@pytest.fixture
def mock_api_recherche_entreprises(mocker):
    return mocker.patch(
        "api.recherche_entreprises.recherche_par_siren",
        return_value=INFOS_ENTREPRISE,
    )


@pytest.fixture
def mock_api_sirene(mocker):
    return mocker.patch(
        "api.sirene.recherche_unite_legale",
        return_value=INFOS_ENTREPRISE,
    )


@pytest.fixture
def mock_api_ratios_financiers(mocker):
    return mocker.patch(
        "api.ratios_financiers.dernier_exercice_comptable",
        return_value={
            "date_cloture_exercice": date(2023, 12, 31),
            "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
            "tranche_chiffre_affaires_consolide": CaracteristiquesAnnuelles.CA_MOINS_DE_60M,
        },
    )
