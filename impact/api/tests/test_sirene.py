from datetime import date

import pytest
from requests.exceptions import Timeout

from api.exceptions import APIError
from api.exceptions import ServerError
from api.exceptions import SirenError
from api.exceptions import TooManyRequestError
from api.sirene import recherche_unite_legale
from api.sirene import SIRENE_TIMEOUT
from api.tests import MockedResponse
from entreprises.models import CaracteristiquesAnnuelles


@pytest.mark.network
def test_api_fonctionnelle():
    SIREN = "130025265"
    infos = recherche_unite_legale(SIREN)

    assert infos == {
        "siren": SIREN,
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499,
        "denomination": "DIRECTION INTERMINISTERIELLE DU NUMERIQUE",
        "categorie_juridique_sirene": 7120,
        "code_pays_etranger_sirene": None,
        "code_NAF": "84.11Z",
    }


def test_succès_avec_résultat_comportant_la_denomination(mocker, settings):
    api_insee_key = "test-key"
    SIREN = "123456789"
    # la plupart des champs inutilisés de la réponse ont été supprimés
    json_content = {
        "header": {"message": "OK", "statut": 200},
        "uniteLegale": {
            "periodesUniteLegale": [
                {
                    "categorieJuridiqueUniteLegale": "5710",
                    "denominationUniteLegale": "ENTREPRISE",
                    "activitePrincipaleUniteLegale": "01.11Z",
                }
            ],
            "siren": "123456789",
            "trancheEffectifsUniteLegale": "20",
        },
    }
    settings.API_SIRENE_KEY = api_insee_key
    faked_request = mocker.patch(
        "requests.get", return_value=MockedResponse(200, json_content)
    )
    capture_message_mock = mocker.patch("sentry_sdk.capture_message")

    infos = recherche_unite_legale(SIREN)

    assert infos["denomination"] == "ENTREPRISE"
    faked_request.assert_called_once_with(
        f"https://api.insee.fr/api-sirene/3.11/siren/123456789?date={date.today().isoformat()}",
        headers={"X-INSEE-Api-Key-Integration": api_insee_key},
        timeout=SIRENE_TIMEOUT,
    )
    capture_message_mock.assert_called_once_with(
        "Code pays étranger non récupéré par l'API sirene"
    )


def test_succès_avec_résultat_sans_la_denomination(mocker):
    SIREN = "478464803"
    # un entrepreneur individuel n'a pas de dénomination mais a un nom
    # le nom complet renvoyé par l'API recherche entreprises est plus complet que le nom
    json_content = {
        "header": {"message": "OK", "statut": 200},
        "uniteLegale": {
            "periodesUniteLegale": [
                {
                    "nomUniteLegale": "COOPER",
                    "categorieJuridiqueUniteLegale": "5710",
                    "denominationUniteLegale": None,
                    "activitePrincipaleUniteLegale": "01.11Z",
                }
            ],
            "siren": "123456789",
            "trancheEffectifsUniteLegale": "20",
        },
    }
    mocker.patch("requests.get", return_value=MockedResponse(200, json_content))

    infos = recherche_unite_legale(SIREN)

    assert infos["denomination"] == "COOPER"


def test_succès_pas_de_résultat(mocker):
    SIREN = "000000000"
    # un siren non trouvé renvoie une 404
    mocker.patch("requests.get", return_value=MockedResponse(404))

    with pytest.raises(SirenError) as e:
        recherche_unite_legale(SIREN)

    assert (
        str(e.value)
        == "L'entreprise n'a pas été trouvée. Vérifiez que le SIREN est correct."
    )


def test_echec_exception_provoquee_par_l_api(mocker):
    """le Timeout est un cas réel mais l'implémentation attrape toutes les erreurs possibles"""
    SIREN = "123456789"
    mocker.patch("requests.get", side_effect=Timeout)
    capture_exception_mock = mocker.patch("sentry_sdk.capture_exception")

    with pytest.raises(APIError) as e:
        recherche_unite_legale(SIREN)

    capture_exception_mock.assert_called_once()
    args, _ = capture_exception_mock.call_args
    assert isinstance(args[0], Timeout)
    assert (
        str(e.value)
        == "Le service est actuellement indisponible. Merci de réessayer plus tard."
    )


def test_echec_trop_de_requetes(mocker):
    SIREN = "123456789"
    mocker.patch("requests.get", return_value=MockedResponse(429))
    capture_message_mock = mocker.patch("sentry_sdk.capture_message")

    with pytest.raises(TooManyRequestError) as e:
        recherche_unite_legale(SIREN)

    capture_message_mock.assert_called_once_with("Trop de requêtes sur l'API sirene")
    assert (
        str(e.value) == "Le service est temporairement surchargé. Merci de réessayer."
    )


def test_echec_erreur_de_l_API(mocker):
    SIREN = "123456789"
    mocker.patch("requests.get", return_value=MockedResponse(500))
    capture_message_mock = mocker.patch("sentry_sdk.capture_message")

    with pytest.raises(ServerError) as e:
        recherche_unite_legale(SIREN)

    capture_message_mock.assert_called_once_with("Erreur API sirene")
    assert (
        str(e.value)
        == "Le service est actuellement indisponible. Merci de réessayer plus tard."
    )


@pytest.mark.parametrize("categorie_juridique", ["", None])
def test_pas_de_categorie_juridique(categorie_juridique, mocker):
    # On se sert de la catégorie juridique pour certaines réglementations qu'on récupère via la catégorie juridique renvoyée par l'API.
    # Normalement toutes les entreprises en ont une.
    # Comme pour l'API recherche entreprises on souhaite être informé si ce n'est pas le cas car le diagnostic pour ces réglementations pourrait être faux.
    SIREN = "123456789"

    json_content = {
        "header": {"message": "OK", "statut": 200},
        "uniteLegale": {
            "periodesUniteLegale": [
                {
                    "categorieJuridiqueUniteLegale": categorie_juridique,
                    "denominationUniteLegale": "ENTREPRISE",
                    "activitePrincipaleUniteLegale": "01.11Z",
                }
            ],
            "siren": "123456789",
            "trancheEffectifsUniteLegale": "20",
        },
    }
    mocker.patch("requests.get", return_value=MockedResponse(200, json_content))
    capture_message_mock = mocker.patch("sentry_sdk.capture_message")

    infos = recherche_unite_legale(SIREN)

    capture_message_mock.assert_any_call(
        "Catégorie juridique récupérée par l'API sirene invalide"
    )
    assert infos["categorie_juridique_sirene"] is None


@pytest.mark.parametrize("activite_principale", ["", None])
def test_pas_d_activite_principale(activite_principale, mocker):
    SIREN = "123456789"

    json_content = {
        "header": {"message": "OK", "statut": 200},
        "uniteLegale": {
            "periodesUniteLegale": [
                {
                    "categorieJuridiqueUniteLegale": "5710",
                    "denominationUniteLegale": "ENTREPRISE",
                    "activitePrincipaleUniteLegale": activite_principale,
                }
            ],
            "siren": "123456789",
            "trancheEffectifsUniteLegale": "20",
        },
    }
    mocker.patch("requests.get", return_value=MockedResponse(200, json_content))

    infos = recherche_unite_legale(SIREN)

    assert infos["code_NAF"] is None
