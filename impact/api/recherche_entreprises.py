from http.client import TOO_MANY_REQUESTS
from xmlrpc.client import SERVER_ERROR

import requests

from .exceptions import APIError
from .exceptions import ServerError
from .exceptions import SirenError
from .exceptions import TooManyRequestError


SIREN_NOT_FOUND_ERROR = (
    "L'entreprise n'a pas été trouvée. Vérifiez que le SIREN est correct."
)
TOO_MANY_REQUESTS_ERROR = "Le service est temporairement surchargé. Merci de réessayer."
SERVER_ERROR = "Le service est actuellement indisponible. Merci de réessayer plus tard."


def recherche(siren):
    # documentation api recherche d'entreprises 1.0.0 https://api.gouv.fr/documentation/api-recherche-entreprises
    url = (
        f"https://recherche-entreprises.api.gouv.fr/search?q={siren}&page=1&per_page=1"
    )
    response = requests.get(url)
    if response.status_code == 200:
        if not response.json()["total_results"]:
            raise SirenError(SIREN_NOT_FOUND_ERROR)

        data = response.json()["results"][0]
        denomination = data["nom_raison_sociale"] or data["nom_complet"]
        try:
            # les tranches d'effectif correspondent à celles de l'API Sirene de l'Insee
            # https://www.sirene.fr/sirene/public/variable/tefen
            tranche_effectif = int(data["tranche_effectif_salarie"])
        except (ValueError, TypeError):
            tranche_effectif = 0
        if tranche_effectif < 21:  # moins de 50 salariés
            taille = "petit"
        elif tranche_effectif < 32:  # moins de 250 salariés
            taille = "moyen"
        elif tranche_effectif < 41:  # moins de 500 salariés
            taille = "grand"
        else:
            taille = "sup500"
        return {
            "siren": siren,
            "effectif": taille,
            "denomination": denomination,
        }
    elif response.status_code == 429:
        raise TooManyRequestError(TOO_MANY_REQUESTS_ERROR)
    elif response.status_code == 400:
        raise APIError(SERVER_ERROR)
    else:
        raise ServerError(SERVER_ERROR)
