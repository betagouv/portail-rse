import requests
import sentry_sdk

from api.exceptions import API_ERROR_SENTRY_MESSAGE
from api.exceptions import APIError

NOM_API = "bilans-ges"
BGES_TIMEOUT = 3


def last_reporting_year(siren):
    try:
        response = requests.get(
            "https://bilans-ges.ademe.fr/api/inventories",
            params={"page": "1", "itemsPerPage": "11", "entity.siren": siren},
            timeout=BGES_TIMEOUT,
        )
    except Exception as e:
        with sentry_sdk.new_scope() as scope:
            scope.set_level("info")
            sentry_sdk.capture_exception(e)
        raise APIError()

    if response.status_code != 200:
        sentry_sdk.capture_message(API_ERROR_SENTRY_MESSAGE.format(NOM_API))
        raise APIError()

    try:
        return extract_last_reporting_year(response.json())
    except Exception as e:
        sentry_sdk.capture_exception(e)
        raise APIError()


def extract_last_reporting_year(json_data) -> int | None:
    # pour réutilisation lors d'extraction des données des tables temporaires
    if members := json_data["hydra:member"]:
        first_member = members[0]
        last_year = first_member["identitySheet"]["reportingYear"]
        for member in members[1:]:
            year = member["identitySheet"]["reportingYear"]
            last_year = max(last_year, year)
        return last_year
