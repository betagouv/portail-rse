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
        # la nature juridique correspond à la nomenclature des catégories juridiques retenue dans a gestion du repertoire Sirene
        # https://www.insee.fr/fr/information/2028129
        try:
            categorie_juridique_sirene = int(data["nature_juridique"])
        except (ValueError, TypeError):
            sentry_sdk.capture_message(
                "Nature juridique récupérée par l'API recherche entreprise invalide"
            )
            categorie_juridique_sirene = None
        try:
            # les tranches d'effectif correspondent à celles de l'API Sirene de l'Insee
            # https://www.sirene.fr/sirene/public/variable/tefen
            tranche_effectif = int(data["tranche_effectif_salarie"])
        except (ValueError, TypeError):
            tranche_effectif = 0
        if tranche_effectif < 11:  # moins de 10 salariés
            effectif = CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10
        elif tranche_effectif < 21:  # moins de 50 salariés
            effectif = CaracteristiquesAnnuelles.EFFECTIF_ENTRE_10_ET_49
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
        try:
            code_pays_etranger = int(data["siege"]["code_pays_etranger"])
        except TypeError:
            code_pays_etranger = None
        except (KeyError, ValueError):
            sentry_sdk.capture_message(
                "Code pays étranger récupéré par l'API recherche entreprise invalide"
            )
            code_pays_etranger = None
        return {
            "siren": siren,
            "effectif": effectif,
            "denomination": denomination,
            "categorie_juridique_sirene": categorie_juridique_sirene,
            "code_pays_etranger_sirene": code_pays_etranger,
        }
    elif response.status_code == 429:
        raise TooManyRequestError(TOO_MANY_REQUESTS_ERROR)
    elif response.status_code == 400:
        sentry_sdk.capture_message("Requête invalide sur l'API recherche entreprise")
        raise APIError(SERVER_ERROR)
    else:
        raise ServerError(SERVER_ERROR)
