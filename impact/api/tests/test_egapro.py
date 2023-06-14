from api.egapro import indicateurs
from api.egapro import is_index_egapro_published


def test_echec_indicateurs(mocker):
    SIREN = "123456789"

    class FakeResponse:
        status_code = 400

    mocker.patch("requests.get", return_value=FakeResponse())
    capture_message_mock = mocker.patch("sentry_sdk.capture_message")

    indicateurs(SIREN, 2023)

    capture_message_mock.assert_called_once_with(
        "Requête invalide sur l'API index EgaPro (indicateurs)"
    )


def test_echec_is_index_egapro_published(mocker):
    SIREN = "123456789"

    class FakeResponse:
        status_code = 400

    mocker.patch("requests.get", return_value=FakeResponse())
    capture_message_mock = mocker.patch("sentry_sdk.capture_message")

    is_index_egapro_published(SIREN, 2023)

    capture_message_mock.assert_called_once_with(
        "Requête invalide sur l'API index EgaPro (is_index_egapro_published)"
    )
