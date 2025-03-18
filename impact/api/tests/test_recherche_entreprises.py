import pytest
from requests.exceptions import Timeout

from api.exceptions import APIError
from api.exceptions import ServerError
from api.exceptions import SirenError
from api.exceptions import TooManyRequestError
from api.recherche_entreprises import recherche
from api.recherche_entreprises import RECHERCHE_ENTREPRISE_TIMEOUT
from entreprises.models import CaracteristiquesAnnuelles
from utils.mock_response import MockedResponse


@pytest.mark.network
def test_api_fonctionnelle():
    SIREN = "130025265"
    infos = recherche(SIREN)

    assert infos == {
        "siren": SIREN,
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499,
        "denomination": "DIRECTION INTERMINISTERIELLE DU NUMERIQUE",
        "categorie_juridique_sirene": 7120,
        "code_pays_etranger_sirene": None,
        "code_NAF": "84.11Z",
    }


def test_succes_recherche_comportant_la_raison_sociale(mocker):
    SIREN = "123456789"
    # la plupart des champs inutilisés de la réponse ont été supprimés
    json_content = {
        "total_results": 1,
        "results": [
            {
                "nom_complet": "entreprise",
                "nom_raison_sociale": "ENTREPRISE",
                "tranche_effectif_salarie": "12",
                "nature_juridique": "5710",
                "siege": {"code_pays_etranger": "99139"},
                "activite_principale": "01.11Z",
            }
        ],
    }
    faked_request = mocker.patch(
        "requests.get", return_value=MockedResponse(200, json_content)
    )

    infos = recherche(SIREN)

    assert infos == {
        "siren": SIREN,
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_10_ET_49,
        "denomination": "ENTREPRISE",
        "categorie_juridique_sirene": 5710,
        "code_pays_etranger_sirene": 99139,
        "code_NAF": "01.11Z",
    }
    faked_request.assert_called_once_with(
        f"https://recherche-entreprises.api.gouv.fr/search?q={SIREN}&page=1&per_page=1&mtm_campaign=portail-rse",
        timeout=RECHERCHE_ENTREPRISE_TIMEOUT,
    )


def test_succes_recherche_sans_la_raison_sociale(mocker):
    SIREN = "123456789"
    json_content = {
        "total_results": 1,
        "results": [
            {
                "nom_complet": "ENTREPRISE",
                "nom_raison_sociale": None,
                "tranche_effectif_salarie": "12",
                "nature_juridique": "5710",
                "siege": {"code_pays_etranger": None},
                "activite_principale": "01.11Z",
            }
        ],
    }
    mocker.patch("requests.get", return_value=MockedResponse(200, json_content))

    infos = recherche(SIREN)

    assert infos["denomination"] == "ENTREPRISE"


def test_succes_pas_de_resultat(mocker):
    SIREN = "123456789"
    json_content = {
        "results": [],
        "total_results": 0,
        "page": 1,
        "per_page": 1,
        "total_pages": 0,
    }
    mocker.patch("requests.get", return_value=MockedResponse(200, json_content))

    with pytest.raises(SirenError) as e:
        recherche(SIREN)

    assert (
        str(e.value)
        == "L'entreprise n'a pas été trouvée. Vérifiez que le SIREN est correct."
    )


def test_echec_recherche_requete_api_invalide(mocker):
    SIREN = "123456789"
    mocker.patch("requests.get", return_value=MockedResponse(400))
    capture_message_mock = mocker.patch("sentry_sdk.capture_message")

    with pytest.raises(APIError) as e:
        recherche(SIREN)

    capture_message_mock.assert_called_once_with(
        "Requête invalide sur l'API recherche entreprises"
    )
    assert (
        str(e.value)
        == "Le service est actuellement indisponible. Merci de réessayer plus tard."
    )


def test_echec_trop_de_requetes(mocker):
    SIREN = "123456789"
    mocker.patch("requests.get", return_value=MockedResponse(429))
    capture_message_mock = mocker.patch("sentry_sdk.capture_message")

    with pytest.raises(TooManyRequestError) as e:
        recherche(SIREN)

    capture_message_mock.assert_called_once_with(
        "Trop de requêtes sur l'API recherche entreprises"
    )
    assert (
        str(e.value) == "Le service est temporairement surchargé. Merci de réessayer."
    )


def test_echec_erreur_de_l_API(mocker):
    SIREN = "123456789"
    mocker.patch("requests.get", return_value=MockedResponse(500))
    capture_message_mock = mocker.patch("sentry_sdk.capture_message")

    with pytest.raises(ServerError) as e:
        recherche(SIREN)

    capture_message_mock.assert_called_once_with("Erreur API recherche entreprises")
    assert (
        str(e.value)
        == "Le service est actuellement indisponible. Merci de réessayer plus tard."
    )


def test_echec_exception_provoquee_par_l_api(mocker):
    """le Timeout est un cas réel mais l'implémentation attrape toutes les erreurs possibles"""
    SIREN = "123456789"
    mocker.patch("requests.get", side_effect=Timeout)
    capture_exception_mock = mocker.patch("sentry_sdk.capture_exception")

    with pytest.raises(APIError) as e:
        recherche(SIREN)

    capture_exception_mock.assert_called_once()
    args, _ = capture_exception_mock.call_args
    assert isinstance(args[0], Timeout)
    assert (
        str(e.value)
        == "Le service est actuellement indisponible. Merci de réessayer plus tard."
    )


def test_entreprise_inexistante_mais_pourtant_retournée_par_l_API(mocker):
    # Le SIREN ne correspond pas à une entreprise réelle mais l'API répond
    # comme si l'entreprise existait. Actuellement, le seul cas connu est le siren 0000000000.
    # On souhaite être informé si ce n'est pas le cas car d'autres cas similaires pourrait être retournés.
    SIREN = "000000000"
    json_content = {
        "total_results": 1,
        "results": [
            {
                "nom_complet": None,
                "nom_raison_sociale": None,
                "tranche_effectif_salarie": "15",
                "nature_juridique": None,
                "nombre_etablissements": 0,
                "nombre_etablissements_ouverts": 0,
                "siege": {},
                "activite_principale": None,
            }
        ],
    }
    mocker.patch("requests.get", return_value=MockedResponse(200, json_content))
    capture_message_mock = mocker.patch("sentry_sdk.capture_message")

    with pytest.raises(SirenError) as e:
        recherche(SIREN)

    assert (
        str(e.value)
        == "L'entreprise n'a pas été trouvée. Vérifiez que le SIREN est correct."
    )
    capture_message_mock.assert_called_once_with(
        "Entreprise inexistante mais retournée par l'API recherche entreprises"
    )


@pytest.mark.parametrize("nature_juridique", ["", None])
def test_pas_de_nature_juridique(nature_juridique, mocker):
    # On se sert de la catégorie juridique pour certaines réglementations qu'on récupère via la nature juridique renvoyée par l'API.
    # Normalement toutes les entreprises en ont une.
    # On souhaite être informé si ce n'est pas le cas car le diagnostic pour ces réglementations pourrait être faux.
    SIREN = "123456789"
    json_content = {
        "total_results": 1,
        "results": [
            {
                "nom_complet": "ENTREPRISE",
                "nom_raison_sociale": None,
                "tranche_effectif_salarie": "15",
                "nature_juridique": nature_juridique,
                "siege": {"code_pays_etranger": None},
                "activite_principale": "01.11Z",
            }
        ],
    }
    mocker.patch("requests.get", return_value=MockedResponse(200, json_content))
    capture_message_mock = mocker.patch("sentry_sdk.capture_message")

    infos = recherche(SIREN)

    capture_message_mock.assert_called_once_with(
        "Nature juridique récupérée par l'API recherche entreprises invalide"
    )
    assert infos["categorie_juridique_sirene"] is None


def test_pas_de_code_pays_etranger(mocker):
    # On souhaite être informé s'il est manquant (utilisé dans la réglementation CSRD).
    SIREN = "123456789"
    json_content = {
        "total_results": 1,
        "results": [
            {
                "nom_complet": "ENTREPRISE",
                "nom_raison_sociale": None,
                "tranche_effectif_salarie": "15",
                "nature_juridique": "5710",
                "siege": {},
                "activite_principale": "01.11Z",
            }
        ],
    }
    mocker.patch("requests.get", return_value=MockedResponse(200, json_content))
    capture_message_mock = mocker.patch("sentry_sdk.capture_message")

    infos = recherche(SIREN)

    capture_message_mock.assert_called_once_with(
        "Code pays étranger récupéré par l'API recherche entreprises invalide"
    )
    assert infos["code_pays_etranger_sirene"] is None


def test_code_pays_etranger_vaut_null_car_en_France(mocker):
    SIREN = "123456789"
    json_content = {
        "total_results": 1,
        "results": [
            {
                "nom_complet": "ENTREPRISE",
                "nom_raison_sociale": None,
                "tranche_effectif_salarie": "15",
                "nature_juridique": "5710",
                "siege": {"code_pays_etranger": None},
                "activite_principale": "01.11Z",
            }
        ],
    }
    mocker.patch("requests.get", return_value=MockedResponse(200, json_content))
    capture_message_mock = mocker.patch("sentry_sdk.capture_message")

    infos = recherche(SIREN)

    assert not capture_message_mock.called
    assert infos["code_pays_etranger_sirene"] is None


@pytest.mark.parametrize("activite_principale", ["", None])
def test_pas_d_activite_principale(activite_principale, mocker):
    SIREN = "123456789"
    json_content = {
        "total_results": 1,
        "results": [
            {
                "nom_complet": "ENTREPRISE",
                "nom_raison_sociale": None,
                "tranche_effectif_salarie": "15",
                "nature_juridique": "5710",
                "siege": {"code_pays_etranger": None},
                "activite_principale": activite_principale,
            }
        ],
    }
    mocker.patch("requests.get", return_value=MockedResponse(200, json_content))

    infos = recherche(SIREN)

    assert infos["code_NAF"] is None
