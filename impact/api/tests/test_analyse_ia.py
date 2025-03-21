import pytest
from requests.exceptions import Timeout

from api.analyse_ia import ANALYSE_IA_TIMEOUT
from api.analyse_ia import lancement_analyse
from api.exceptions import APIError
from utils.mock_response import MockedResponse

DOCUMENT_ID = 1
DOCUMENT_URL = "https://document.test"
CALLBACK_URL = "https://callback.test"


def test_succès_lancement_analyse(mocker, settings):
    settings.API_ANALYSE_IA_BASE_URL = (
        API_ANALYSE_IA_BASE_URL
    ) = "https://analyse-ia.test"
    settings.API_ANALYSE_IA_TOKEN = API_ANALYSE_IA_TOKEN = "TOKEN"
    json_content = {"status": "processing"}
    faked_request = mocker.patch(
        "requests.post", return_value=MockedResponse(200, json_content)
    )

    etat = lancement_analyse(DOCUMENT_ID, DOCUMENT_URL, CALLBACK_URL)

    assert etat == "processing"
    faked_request.assert_called_once_with(
        f"{API_ANALYSE_IA_BASE_URL}/run-task",
        {
            "document_id": DOCUMENT_ID,
            "document_url": DOCUMENT_URL,
            "callback_url": CALLBACK_URL,
        },
        headers={"Authorization": f"Bearer {API_ANALYSE_IA_TOKEN}"},
        timeout=ANALYSE_IA_TIMEOUT,
    )


def test_echec_exception_provoquee_par_l_api(mocker):
    """le Timeout est un cas réel mais l'implémentation attrape toutes les erreurs possibles"""
    mocker.patch("requests.post", side_effect=Timeout)
    capture_exception_mock = mocker.patch("sentry_sdk.capture_exception")

    with pytest.raises(APIError) as e:
        lancement_analyse(DOCUMENT_ID, DOCUMENT_URL, CALLBACK_URL)

    capture_exception_mock.assert_called_once()
    args, _ = capture_exception_mock.call_args
    assert isinstance(args[0], Timeout)
    assert (
        str(e.value)
        == "Le service est actuellement indisponible. Merci de réessayer plus tard."
    )


def test_echec_erreur_de_l_API(mocker):
    mocker.patch("requests.post", return_value=MockedResponse(500))
    capture_message_mock = mocker.patch("sentry_sdk.capture_message")

    with pytest.raises(APIError) as e:
        lancement_analyse(DOCUMENT_ID, DOCUMENT_URL, CALLBACK_URL)

    capture_message_mock.assert_called_once_with("Erreur API analyse IA")
    assert (
        str(e.value)
        == "Le service est actuellement indisponible. Merci de réessayer plus tard."
    )


def test_succès_lancement_analyse_mais_status_manquant(mocker):
    json_content = {}
    faked_request = mocker.patch(
        "requests.post", return_value=MockedResponse(200, json_content)
    )
    capture_message_mock = mocker.patch("sentry_sdk.capture_message")

    etat = lancement_analyse(DOCUMENT_ID, DOCUMENT_URL, CALLBACK_URL)

    assert etat == "inconnu"
    capture_message_mock.assert_called_once_with(
        "État récupéré par l'API analyse IA invalide"
    )
