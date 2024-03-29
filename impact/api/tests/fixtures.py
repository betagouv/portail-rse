from datetime import date

import pytest

from entreprises.models import CaracteristiquesAnnuelles


@pytest.fixture
def mock_api_recherche_entreprises(mocker):
    return mocker.patch(
        "api.recherche_entreprises.recherche",
        return_value={
            "siren": "000000001",
            "denomination": "Entreprise SAS",
            "effectif": CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
            "categorie_juridique_sirene": 5710,
            "code_pays_etranger_sirene": None,
        },
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


@pytest.fixture
def mock_api_egapro(mocker):
    mocker.patch(
        "api.egapro.indicateurs_bdese",
        return_value={
            "nombre_femmes_plus_hautes_remunerations": None,
            "objectifs_progression": None,
        },
    )
    return mocker.patch(
        "api.egapro.is_index_egapro_published",
        return_value=False,
    )


@pytest.fixture
def mock_api_bges(mocker):
    return mocker.patch("api.bges.last_reporting_year", return_value=None)
