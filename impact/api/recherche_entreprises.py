from xmlrpc.client import SERVER_ERROR

import requests
import sentry_sdk

from .exceptions import APIError
from .exceptions import ServerError
from .exceptions import SirenError
from .exceptions import TooManyRequestError
from entreprises.models import CaracteristiquesAnnuelles

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
            effectif = CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50
        elif tranche_effectif < 32:  # moins de 250 salariés
            effectif = CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249
        # la tranche EFFECTIF_ENTRE_250_ET_299 ne peut pas être trouvée avec l'API
        elif tranche_effectif < 41:  # moins de 500 salariés
            effectif = CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499
        elif tranche_effectif < 52:  # moins de 5 000 salariés:
            effectif = CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999
        elif tranche_effectif == 52:
            effectif = CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999
        else:
            effectif = CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS
        return {
            "siren": siren,
            "effectif": effectif,
            "denomination": denomination,
        }
    elif response.status_code == 429:
        raise TooManyRequestError(TOO_MANY_REQUESTS_ERROR)
    elif response.status_code == 400:
        sentry_sdk.capture_message("Requête invalide sur l'API recherche entreprise")
        raise APIError(SERVER_ERROR)
    else:
        raise ServerError(SERVER_ERROR)
