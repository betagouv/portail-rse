from datetime import date
from unittest import mock

import pytest
from requests.exceptions import Timeout

from api.exceptions import APIError
from api.exceptions import ServerError
from api.exceptions import SirenError
from api.exceptions import TooManyRequestError
from api.sirene import RECHERCHE_ENTREPRISE_TIMEOUT
from api.sirene import recherche_unite_legale
from entreprises.models import CaracteristiquesAnnuelles


@pytest.mark.network
def test_api_fonctionnelle():
    SIREN = "130025265"
    infos = recherche_unite_legale(SIREN)

    assert infos == {
        "siren": SIREN,
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "denomination": "DIRECTION INTERMINISTERIELLE DU NUMERIQUE",
        "categorie_juridique_sirene": 7120,
        "code_pays_etranger_sirene": None,
    }


def test_succès_avec_résultat(mocker):
    SIREN = "123456789"

    class FakeResponse:
        status_code = 200

        def json(self):
            # la plupart des champs inutilisés de la réponse ont été supprimés
            return {
                "header": {"message": "OK", "statut": 200},
                "uniteLegale": {
                    "periodesUniteLegale": [
                        {
                            "categorieJuridiqueUniteLegale": "5710",
                            "denominationUniteLegale": "ENTREPRISE",
                        }
                    ],
                    "siren": "123456789",
                    "trancheEffectifsUniteLegale": "20",
                },
            }

    faked_request = mocker.patch("requests.get", return_value=FakeResponse())

    infos = recherche_unite_legale(SIREN)

    assert infos == {
        "siren": SIREN,
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_10_ET_49,
        "denomination": "ENTREPRISE",
        "categorie_juridique_sirene": 5710,
        "code_pays_etranger_sirene": None,
    }
    faked_request.assert_called_once_with(
        f"https://api.insee.fr/entreprises/sirene/V3.11/siren/123456789?date={date.today().isoformat()}",
        headers={"Authorization": mock.ANY},
        timeout=RECHERCHE_ENTREPRISE_TIMEOUT,
    )


def test_succès_pas_de_résultat(mocker):
    SIREN = "000000000"

    class FakeResponse:
        status_code = 404

    faked_request = mocker.patch("requests.get", return_value=FakeResponse())

    with pytest.raises(SirenError) as e:
        recherche_unite_legale(SIREN)

    faked_request.assert_called_once_with(
        f"https://api.insee.fr/entreprises/sirene/V3.11/siren/000000000?date={date.today().isoformat()}",
        headers={"Authorization": mock.ANY},
        timeout=RECHERCHE_ENTREPRISE_TIMEOUT,
    )
    assert (
        str(e.value)
        == "L'entreprise n'a pas été trouvée. Vérifiez que le SIREN est correct."
    )


def test_echec_exception_provoquee_par_l_api(mocker):
    """le Timeout est un cas réel mais l'implémentation attrape toutes les erreurs possibles"""
    SIREN = "123456789"

    faked_request = mocker.patch("requests.get", side_effect=Timeout)
    capture_exception_mock = mocker.patch("sentry_sdk.capture_exception")

    with pytest.raises(APIError) as e:
        recherche_unite_legale(SIREN)

    capture_exception_mock.assert_called_once()
    args, _ = capture_exception_mock.call_args
    assert type(args[0]) == Timeout
    assert (
        str(e.value)
        == "Le service est actuellement indisponible. Merci de réessayer plus tard."
    )


def test_echec_trop_de_requetes(mocker):
    SIREN = "123456789"

    class FakeResponse:
        status_code = 429

    mocker.patch("requests.get", return_value=FakeResponse())
    capture_message_mock = mocker.patch("sentry_sdk.capture_message")

    with pytest.raises(TooManyRequestError) as e:
        recherche_unite_legale(SIREN)

    capture_message_mock.assert_called_once_with(
        "Trop de requêtes sur l'API recherche unité légale"
    )
    assert (
        str(e.value) == "Le service est temporairement surchargé. Merci de réessayer."
    )


def test_echec_erreur_de_l_API(mocker):
    SIREN = "123456789"

    class FakeResponse:
        status_code = 500

    mocker.patch("requests.get", return_value=FakeResponse())
    capture_message_mock = mocker.patch("sentry_sdk.capture_message")

    with pytest.raises(ServerError) as e:
        recherche_unite_legale(SIREN)

    capture_message_mock.assert_called_once_with("Erreur API recherche unité légale")
    assert (
        str(e.value)
        == "Le service est actuellement indisponible. Merci de réessayer plus tard."
    )
