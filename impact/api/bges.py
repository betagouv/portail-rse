from datetime import datetime

import requests
import sentry_sdk

from api.exceptions import API_ERROR_SENTRY_MESSAGE
from api.exceptions import APIError

NOM_API = "bilans-ges"
BGES_TIMEOUT = 10


def dernier_bilan_ges(siren):
    try:
        response = requests.get(
            "https://bilans-ges.ademe.fr/api/inventories",
            params={"page": "1", "itemsPerPage": "11", "entity.siren": siren},
            timeout=BGES_TIMEOUT,
        )
    except Exception as e:
        with sentry_sdk.push_scope() as scope:
            scope.set_level("info")
            sentry_sdk.capture_exception(e)
        raise APIError()

    if response.status_code != 200:
        sentry_sdk.capture_message(API_ERROR_SENTRY_MESSAGE.format(NOM_API))
        raise APIError()

    try:
        data = response.json()
        if members := data["hydra:member"]:
            first_member = members[0]
            last_reporting_year = first_member["identitySheet"]["reportingYear"]
            publicated_at = first_member["publication"]["publicatedAt"]
            for member in members[1:]:
                year = member["identitySheet"]["reportingYear"]
                if year > last_reporting_year:
                    last_reporting_year = year
                    publicated_at = member["publication"]["publicatedAt"]
            return {
                "annee_reporting": last_reporting_year,
                "date_publication": datetime.fromisoformat(publicated_at).date(),
            }
    except Exception as e:
        sentry_sdk.capture_exception(e)
        raise APIError()
