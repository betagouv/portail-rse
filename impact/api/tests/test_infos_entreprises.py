from datetime import date

import pytest

from api.exceptions import APIError
from api.exceptions import SirenError
from api.infos_entreprise import infos_entreprise
from api.infos_entreprise import recherche_par_nom_ou_siren
from entreprises.models import CaracteristiquesAnnuelles

SIREN = "123456789"
INFOS_ENTREPRISE = {
    "siren": "000000001",
    "denomination": "Entreprise SAS",
    "effectif": CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
    "categorie_juridique_sirene": 5710,
    "code_pays_etranger_sirene": None,
    "code_NAF": "01.11Z",
}
INFOS_FINANCIERES = {
    "date_cloture_exercice": date(2023, 12, 31),
    "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
    "tranche_chiffre_affaires_consolide": CaracteristiquesAnnuelles.CA_MOINS_DE_60M,
}
RECHERCHE = "Danone"
ENTREPRISES_TROUVEES = [
    {
        "siren": "000000001",
        "denomination": "Entreprise Test 1",
        "activité": "Cultures non permanentes",
    },
    {
        "siren": "889297453",
        "denomination": "YAAL COOP",
        "activité": "Programmation, conseil et autres activités informatiques",
    },
    {
        "siren": "552032534",
        "denomination": "DANONE",
        "activité": "Activités des sièges sociaux",
    },
]
RESULTATS_RECHERCHE = {
    "nombre_resultats": 3,
    "entreprises": ENTREPRISES_TROUVEES,
}


@pytest.fixture
def mock_api_recherche_par_siren(mocker):
    return mocker.patch(
        "api.recherche_entreprises.recherche_par_siren",
    )


@pytest.fixture
def mock_api_sirene(mocker):
    return mocker.patch("api.sirene.recherche_unite_legale_par_siren")


@pytest.fixture
def mock_api_ratios_financiers(mocker):
    return mocker.patch("api.ratios_financiers.dernier_exercice_comptable")


@pytest.fixture
def mock_api_recherche_textuelle(mocker):
    return mocker.patch("api.recherche_entreprises.recherche_textuelle")


@pytest.fixture
def mock_api_recherche_unites_legales_par_nom_ou_siren(mocker):
    return mocker.patch("api.sirene.recherche_unites_legales_par_nom_ou_siren")


def test_infos_entreprise_succes_api_recherche_entreprises(
    mock_api_recherche_par_siren, mock_api_sirene, mock_api_ratios_financiers
):
    mock_api_recherche_par_siren.return_value = INFOS_ENTREPRISE
    infos = infos_entreprise(SIREN)

    mock_api_recherche_par_siren.assert_called_once_with(SIREN)
    assert not mock_api_sirene.called
    assert not mock_api_ratios_financiers.called
    assert infos == INFOS_ENTREPRISE


def test_infos_entreprise_echec_api_recherche_entreprises_erreur_de_l_api_puis_succes_api_sirene(
    mock_api_recherche_par_siren, mock_api_sirene
):
    mock_api_recherche_par_siren.side_effect = APIError
    mock_api_sirene.return_value = INFOS_ENTREPRISE
    infos = infos_entreprise(SIREN)

    mock_api_recherche_par_siren.assert_called_once_with(SIREN)
    mock_api_sirene.assert_called_once_with(SIREN)
    assert infos == INFOS_ENTREPRISE


def test_infos_entreprise_echec_api_recherche_entreprises_siren_invalide(
    mock_api_recherche_par_siren, mock_api_sirene
):
    mock_api_recherche_par_siren.side_effect = SirenError("Message d'erreur")

    with pytest.raises(SirenError) as e:
        infos_entreprise(SIREN)

    mock_api_recherche_par_siren.assert_called_once_with(SIREN)
    assert not mock_api_sirene.called
    assert str(e.value) == "Message d'erreur"


def test_infos_entreprise_echecs_api_recherche_entreprises_et_api_sirene(
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
    mock_api_recherche_par_siren.return_value = INFOS_ENTREPRISE
    mock_api_ratios_financiers.return_value = INFOS_FINANCIERES
    infos = infos_entreprise(SIREN, donnees_financieres=True)

    mock_api_recherche_par_siren.assert_called_once_with(SIREN)
    mock_api_ratios_financiers.assert_called_once_with(SIREN)
    assert infos == INFOS_ENTREPRISE | INFOS_FINANCIERES


def test_infos_entreprise_echec_de_l_API_ratios_financiers_non_bloquant(
    mock_api_recherche_par_siren, mock_api_ratios_financiers
):
    mock_api_recherche_par_siren.return_value = INFOS_ENTREPRISE
    mock_api_ratios_financiers.side_effect = APIError("Message d'erreur")

    infos = infos_entreprise(SIREN, donnees_financieres=True)

    mock_api_recherche_par_siren.assert_called_once_with(SIREN)
    mock_api_ratios_financiers.assert_called_once_with(SIREN)
    assert infos == INFOS_ENTREPRISE | {
        "date_cloture_exercice": None,
        "tranche_chiffre_affaires": None,
        "tranche_chiffre_affaires_consolide": None,
    }


def test_recherche_par_nom_ou_siren_succes_api_recherche_entreprises(
    mock_api_recherche_textuelle, mock_api_recherche_unites_legales_par_nom_ou_siren
):
    mock_api_recherche_textuelle.return_value = RESULTATS_RECHERCHE

    resultats = recherche_par_nom_ou_siren(RECHERCHE)

    mock_api_recherche_textuelle.assert_called_once_with(RECHERCHE)
    assert resultats == RESULTATS_RECHERCHE
    assert not mock_api_recherche_unites_legales_par_nom_ou_siren.called


def test_recherche_par_nom_ou_siren_echec_api_recherche_entreprises_erreur_de_l_api_puis_succes_api_sirene(
    mock_api_recherche_textuelle, mock_api_recherche_unites_legales_par_nom_ou_siren
):
    mock_api_recherche_textuelle.side_effect = APIError()
    mock_api_recherche_unites_legales_par_nom_ou_siren.return_value = (
        RESULTATS_RECHERCHE
    )

    resultats = recherche_par_nom_ou_siren(RECHERCHE)

    mock_api_recherche_textuelle.assert_called_once_with(RECHERCHE)
    mock_api_recherche_unites_legales_par_nom_ou_siren.assert_called_once_with(
        RECHERCHE
    )
    assert resultats == RESULTATS_RECHERCHE


def test_recherche_par_nom_ou_siren_echecs_api_recherche_entreprises_et_api_sirene(
    mock_api_recherche_textuelle, mock_api_recherche_unites_legales_par_nom_ou_siren
):
    mock_api_recherche_textuelle.side_effect = APIError(
        "Message d'erreur recherche entreprises"
    )
    mock_api_recherche_unites_legales_par_nom_ou_siren.side_effect = APIError(
        "Message d'erreur sirene"
    )

    with pytest.raises(APIError) as e:
        resultats = recherche_par_nom_ou_siren(RECHERCHE)

    mock_api_recherche_textuelle.assert_called_once_with(RECHERCHE)
    mock_api_recherche_unites_legales_par_nom_ou_siren.assert_called_once_with(
        RECHERCHE
    )
    assert str(e.value) == "Message d'erreur sirene"
