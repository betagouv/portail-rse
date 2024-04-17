import requests
import sentry_sdk

from api.exceptions import APIError
from api.exceptions import SERVER_ERROR
from api.exceptions import ServerError
from api.exceptions import SIREN_NOT_FOUND_ERROR
from api.exceptions import SirenError
from api.exceptions import TOO_MANY_REQUESTS_ERROR
from api.exceptions import TooManyRequestError
from api.sirene import convertit_tranche_effectif

RECHERCHE_ENTREPRISE_TIMEOUT = 10


def recherche(siren):
    # documentation api recherche d'entreprises 1.0.0 https://api.gouv.fr/documentation/api-recherche-entreprises
    try:
        url = f"https://recherche-entreprises.api.gouv.fr/search?q={siren}&page=1&per_page=1"
        response = requests.get(url, timeout=RECHERCHE_ENTREPRISE_TIMEOUT)
    except Exception as e:
        with sentry_sdk.push_scope() as scope:
            scope.set_level("info")
            sentry_sdk.capture_exception(e)
        raise APIError(SERVER_ERROR)

    if response.status_code == 200:
        if not response.json()["total_results"]:
            raise SirenError(SIREN_NOT_FOUND_ERROR)

        data = response.json()["results"][0]

        denomination = data["nom_raison_sociale"] or data["nom_complet"]
        if not denomination:
            sentry_sdk.capture_message(
                "Entreprise inexistante mais retournée par l'API recherche entreprises"
            )
            raise SirenError(SIREN_NOT_FOUND_ERROR)

        # la nature juridique correspond à la nomenclature des catégories juridiques retenue dans la gestion du repertoire Sirene
        # https://www.insee.fr/fr/information/2028129
        try:
            categorie_juridique_sirene = int(data["nature_juridique"])
        except (ValueError, TypeError):
            sentry_sdk.capture_message(
                "Nature juridique récupérée par l'API recherche entreprises invalide"
            )
            categorie_juridique_sirene = None

        effectif = convertit_tranche_effectif(data["tranche_effectif_salarie"])

        try:
            code_pays_etranger = int(data["siege"]["code_pays_etranger"])
        except TypeError:
            code_pays_etranger = None
        except (KeyError, ValueError):
            sentry_sdk.capture_message(
                "Code pays étranger récupéré par l'API recherche entreprises invalide"
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
        sentry_sdk.capture_message("Trop de requêtes sur l'API recherche entreprises")
        raise TooManyRequestError(TOO_MANY_REQUESTS_ERROR)
    elif response.status_code == 400:
        sentry_sdk.capture_message("Requête invalide sur l'API recherche entreprises")
        raise APIError(SERVER_ERROR)
    else:
        sentry_sdk.capture_message("Erreur API recherche entreprises")
        raise ServerError(SERVER_ERROR)
