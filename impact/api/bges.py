import requests
import sentry_sdk


def bges_publication_year(siren):
    response = requests.get(
        "https://bilans-ges.ademe.fr/api/inventories",
        params={"page": "1", "itemsPerPage": "11", "entity.siren": siren},
    )
    if response.status_code != 200:
        sentry_sdk.capture_message("Erreur API bilans-ges")
        return

    data = response.json()
    if members := data["hydra:member"]:
        first_member = members[0]
        last_year = first_member["identitySheet"]["reportingYear"]
        for member in members[1:]:
            year = member["identitySheet"]["reportingYear"]
            last_year = max(last_year, year)
        return last_year