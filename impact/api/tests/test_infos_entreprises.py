from datetime import date

import pytest

from api.exceptions import APIError
from api.exceptions import SirenError
from api.infos_entreprise import infos_entreprise
from entreprises.models import CaracteristiquesAnnuelles

SIREN = "123456789"


def test_infos_entreprise_succes_api_recherche_entreprises(
    mock_api_recherche_par_siren, mock_api_sirene, mock_api_ratios_financiers
):
    mock_api_recherche_par_siren.return_value = {
        "siren": SIREN,
        "denomination": "Entreprise SAS",
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        "categorie_juridique_sirene": 5710,
        "code_pays_etranger_sirene": None,
        "code_NAF": "01.11Z",
    }
    infos = infos_entreprise(SIREN)

    mock_api_recherche_par_siren.assert_called_once_with(SIREN)
    assert not mock_api_sirene.called
    assert not mock_api_ratios_financiers.called
    assert infos == {
        "siren": SIREN,
        "denomination": "Entreprise SAS",
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        "categorie_juridique_sirene": 5710,
        "code_pays_etranger_sirene": None,
        "code_NAF": "01.11Z",
    }


def test_infos_entreprise_echec_api_recherche_entreprises_erreur_de_l_api_puis_succes_api_sirene(
    mock_api_recherche_par_siren, mock_api_sirene
):
    mock_api_recherche_par_siren.side_effect = APIError
    mock_api_sirene.return_value = {
        "siren": SIREN,
        "denomination": "Entreprise SAS",
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        "categorie_juridique_sirene": 5710,
        "code_pays_etranger_sirene": None,
        "code_NAF": "01.11Z",
    }
    infos = infos_entreprise(SIREN)

    mock_api_recherche_par_siren.assert_called_once_with(SIREN)
    mock_api_sirene.assert_called_once_with(SIREN)
    assert infos == {
        "siren": SIREN,
        "denomination": "Entreprise SAS",
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        "categorie_juridique_sirene": 5710,
        "code_pays_etranger_sirene": None,
        "code_NAF": "01.11Z",
    }


def test_infos_entreprise_echec_api_recherche_entreprises_siren_invalide(
    mock_api_recherche_par_siren, mock_api_sirene
):
    mock_api_recherche_par_siren.side_effect = SirenError("Message d'erreur")

    with pytest.raises(SirenError) as e:
        infos_entreprise(SIREN)

    mock_api_recherche_par_siren.assert_called_once_with(SIREN)
    assert not mock_api_sirene.called
    assert str(e.value) == "Message d'erreur"


def test_infos_entreprise_echec_api_recherche_entreprises_et_api_sirene(
    mock_api_recherche_par_siren, mock_api_sirene
):
    mock_api_recherche_par_siren.side_effect = APIError(
        "Message d'erreur recherche entreprises"
    )
    mock_api_sirene.side_effect = APIError("Message d'erreur sirene")

    with pytest.raises(APIError) as e:
        infos_entreprise(SIREN)

    mock_api_recherche_par_siren.assert_called_once_with(SIREN)
    mock_api_sirene.assert_called_once_with(SIREN)
    assert str(e.value) == "Message d'erreur sirene"


def test_infos_entreprise_incluant_les_données_financières(
    mock_api_recherche_par_siren, mock_api_ratios_financiers
):
    mock_api_recherche_par_siren.return_value = {
        "siren": SIREN,
        "denomination": "Entreprise SAS",
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        "categorie_juridique_sirene": 5710,
        "code_pays_etranger_sirene": None,
        "code_NAF": "01.11Z",
    }
    mock_api_ratios_financiers.return_value = {
        "date_cloture_exercice": date(2023, 12, 31),
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
        "tranche_chiffre_affaires_consolide": CaracteristiquesAnnuelles.CA_MOINS_DE_60M,
    }

    infos = infos_entreprise(SIREN, donnees_financieres=True)

    mock_api_recherche_par_siren.assert_called_once_with(SIREN)
    mock_api_ratios_financiers.assert_called_once_with(SIREN)
    assert infos == {
        "siren": SIREN,
        "denomination": "Entreprise SAS",
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        "categorie_juridique_sirene": 5710,
        "code_pays_etranger_sirene": None,
        "code_NAF": "01.11Z",
        "date_cloture_exercice": date(2023, 12, 31),
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
        "tranche_chiffre_affaires_consolide": CaracteristiquesAnnuelles.CA_MOINS_DE_60M,
    }


def test_infos_entreprise_echec_de_l_API_ratios_financiers_non_bloquant(
    mock_api_recherche_par_siren, mock_api_ratios_financiers
):
    mock_api_recherche_par_siren.return_value = {
        "siren": SIREN,
        "denomination": "Entreprise SAS",
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        "categorie_juridique_sirene": 5710,
        "code_pays_etranger_sirene": None,
        "code_NAF": "01.11Z",
    }
    mock_api_ratios_financiers.side_effect = APIError("Message d'erreur")

    infos = infos_entreprise(SIREN, donnees_financieres=True)

    mock_api_recherche_par_siren.assert_called_once_with(SIREN)
    mock_api_ratios_financiers.assert_called_once_with(SIREN)
    assert infos == {
        "siren": SIREN,
        "denomination": "Entreprise SAS",
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        "categorie_juridique_sirene": 5710,
        "code_pays_etranger_sirene": None,
        "code_NAF": "01.11Z",
        "date_cloture_exercice": None,
        "tranche_chiffre_affaires": None,
        "tranche_chiffre_affaires_consolide": None,
    }
