import pytest

from api.exceptions import APIError
from api.recherche_entreprises import recherche


def test_succes_recherche(client, mocker):
    SIREN = "123456789"

    class FakeResponse:
        status_code = 200

        def json(self):
            return {
                "total_results": 1,
                "results": [
                    {
                        "nom_raison_sociale": "ENTREPRISE",
                        "tranche_effectif_salarie": "15",
                    }
                ],
            }

    with mocker.patch("requests.get", return_value=FakeResponse()):
        infos = recherche(SIREN)

    assert infos == {
        "siren": SIREN,
        "effectif": "petit",
        "raison_sociale": "ENTREPRISE",
    }


def test_echec_recherche(client, mocker):
    SIREN = "123456789"

    class FakeResponse:
        status_code = 400

    with mocker.patch("requests.get", return_value=FakeResponse()), pytest.raises(
        APIError
    ):
        infos = recherche(SIREN)
