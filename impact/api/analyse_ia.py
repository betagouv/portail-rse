import requests
import sentry_sdk
from django.conf import settings

from api.exceptions import API_ERROR_SENTRY_MESSAGE
from api.exceptions import APIError
from api.exceptions import SERVER_ERROR

NOM_API = "analyse IA"
ANALYSE_IA_TIMEOUT = 10


def lancement_analyse(document_id, document_url, callback_url):
    try:
        url = f"{settings.API_ANALYSE_IA_BASE_URL}/run-task"
        response = requests.post(
            url,
            {
                "document_id": document_id,
                "document_url": document_url,
                "callback_url": callback_url,
            },
            headers={"Authorization": f"Bearer {settings.API_ANALYSE_IA_TOKEN}"},
            timeout=ANALYSE_IA_TIMEOUT,
        )
    except Exception as e:
        sentry_sdk.capture_exception(e)
        raise APIError(SERVER_ERROR)

    if response.status_code == 200:
        try:
            etat = response.json()["status"]
        except KeyError:
            sentry_sdk.capture_message(f"État récupéré par l'API {NOM_API} invalide")
            etat = "inconnu"
    else:
        sentry_sdk.capture_message(API_ERROR_SENTRY_MESSAGE.format(NOM_API))
        raise APIError(SERVER_ERROR)
    return etat
