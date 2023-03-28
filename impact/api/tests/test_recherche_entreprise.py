import pytest

from api.exceptions import APIError
from api.recherche_entreprises import recherche


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
        "effectif": "petit",
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
        "effectif": "petit",
        "denomination": "ENTREPRISE",
    }


def test_echec_recherche(mocker):
    SIREN = "123456789"

    class FakeResponse:
        status_code = 400

    mocker.patch("requests.get", return_value=FakeResponse())
    with pytest.raises(APIError):
        recherche(SIREN)
