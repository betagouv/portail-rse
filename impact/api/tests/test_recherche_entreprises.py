import pytest

from api.exceptions import APIError
from api.exceptions import ServerError
from api.exceptions import SirenError
from api.exceptions import TooManyRequestError
from api.recherche_entreprises import recherche
from entreprises.models import CaracteristiquesAnnuelles


def test_succes_recherche_comportant_la_raison_sociale(mocker):
    SIREN = "123456789"

    class FakeResponse:
        status_code = 200

        def json(self):
            return {
                "total_results": 1,
                "results": [
                    {
                        "nom_complet": "entreprise",
                        "nom_raison_sociale": "ENTREPRISE",
                        "tranche_effectif_salarie": "15",
                    }
                ],
            }

    mocker.patch("requests.get", return_value=FakeResponse())
    infos = recherche(SIREN)

    assert infos == {
        "siren": SIREN,
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50,
        "denomination": "ENTREPRISE",
    }


def test_succes_recherche_sans_la_raison_sociale(mocker):
    SIREN = "123456789"

    class FakeResponse:
        status_code = 200

        def json(self):
            return {
                "total_results": 1,
                "results": [
                    {
                        "nom_complet": "ENTREPRISE",
                        "nom_raison_sociale": None,
                        "tranche_effectif_salarie": "15",
                    }
                ],
            }

    mocker.patch("requests.get", return_value=FakeResponse())
    infos = recherche(SIREN)

    assert infos == {
        "siren": SIREN,
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50,
        "denomination": "ENTREPRISE",
    }


def test_succes_pas_de_resultat(mocker):
    SIREN = "123456789"

    class FakeResponse:
        status_code = 200

        def json(self):
            return {
                "results": [],
                "total_results": 0,
                "page": 1,
                "per_page": 1,
                "total_pages": 0,
            }

    mocker.patch("requests.get", return_value=FakeResponse())
    with pytest.raises(SirenError) as e:
        recherche(SIREN)

    assert (
        str(e.value)
        == "L'entreprise n'a pas été trouvée. Vérifiez que le SIREN est correct."
    )


def test_echec_recherche(mocker):
    SIREN = "123456789"

    class FakeResponse:
        status_code = 400

    mocker.patch("requests.get", return_value=FakeResponse())
    capture_message_mock = mocker.patch("sentry_sdk.capture_message")
    with pytest.raises(APIError) as e:
        recherche(SIREN)

    capture_message_mock.assert_called_once_with(
        "Requête invalide sur l'API recherche entreprise"
    )
    assert (
        str(e.value)
        == "Le service est actuellement indisponible. Merci de réessayer plus tard."
    )


def test_echec_trop_de_requetes(mocker):
    SIREN = "123456789"

    class FakeResponse:
        status_code = 429

    mocker.patch("requests.get", return_value=FakeResponse())
    with pytest.raises(TooManyRequestError) as e:
        recherche(SIREN)

    assert (
        str(e.value) == "Le service est temporairement surchargé. Merci de réessayer."
    )


def test_echec_erreur_de_l_API(mocker):
    SIREN = "123456789"

    class FakeResponse:
        status_code = 500

    mocker.patch("requests.get", return_value=FakeResponse())
    with pytest.raises(ServerError) as e:
        recherche(SIREN)

    assert (
        str(e.value)
        == "Le service est actuellement indisponible. Merci de réessayer plus tard."
    )
