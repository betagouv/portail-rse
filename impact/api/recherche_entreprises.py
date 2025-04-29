import requests
import sentry_sdk

from api.exceptions import API_ERROR_SENTRY_MESSAGE
from api.exceptions import APIError
from api.exceptions import INVALID_REQUEST_SENTRY_MESSAGE
from api.exceptions import SERVER_ERROR
from api.exceptions import ServerError
from api.exceptions import SIREN_NOT_FOUND_ERROR
from api.exceptions import SirenError
from api.exceptions import TOO_MANY_REQUESTS_ERROR
from api.exceptions import TOO_MANY_REQUESTS_SENTRY_MESSAGE
from api.exceptions import TooManyRequestError
from api.sirene import convertit_code_NAF
from api.sirene import convertit_tranche_effectif

NOM_API = "recherche entreprises"
RECHERCHE_ENTREPRISE_TIMEOUT = 10

# documentation api recherche d'entreprises 1.0.0 https://www.data.gouv.fr/fr/dataservices/api-recherche-dentreprises/


def recherche_par_siren(siren):
    try:
        url = f"https://recherche-entreprises.api.gouv.fr/search?q={siren}&page=1&per_page=1&mtm_campaign=portail-rse"
        response = requests.get(url, timeout=RECHERCHE_ENTREPRISE_TIMEOUT)
    except Exception as e:
        with sentry_sdk.new_scope() as scope:
            scope.set_level("info")
            sentry_sdk.capture_exception(e)
        raise APIError(SERVER_ERROR)

    match response.status_code:
        case 200:
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

            code_NAF = data["activite_principale"] or None

            return {
                "siren": siren,
                "effectif": effectif,
                "denomination": denomination,
                "categorie_juridique_sirene": categorie_juridique_sirene,
                "code_pays_etranger_sirene": code_pays_etranger,
                "code_NAF": code_NAF,
            }
        case 429:
            sentry_sdk.capture_message(TOO_MANY_REQUESTS_SENTRY_MESSAGE.format(NOM_API))
            raise TooManyRequestError(TOO_MANY_REQUESTS_ERROR)
        case 400:
            sentry_sdk.capture_message(INVALID_REQUEST_SENTRY_MESSAGE.format(NOM_API))
            raise APIError(SERVER_ERROR)
        case _:
            sentry_sdk.capture_message(API_ERROR_SENTRY_MESSAGE.format(NOM_API))
            raise ServerError(SERVER_ERROR)


def recherche_textuelle(recherche):
    url = "https://recherche-entreprises.api.gouv.fr/search"
    params = {
        "q": recherche,
        "minimal": True,
        "page": 1,
        "per_page": 5,
        "mtm_campaign": "portail-rse",
    }

    try:
        response = requests.get(
            url, params=params, timeout=RECHERCHE_ENTREPRISE_TIMEOUT
        )
    except Exception as e:
        with sentry_sdk.new_scope() as scope:
            scope.set_level("info")
            sentry_sdk.capture_exception(e)
        raise APIError(SERVER_ERROR)

    match response.status_code:
        case 200:
            if nombre_resultats := response.json()["total_results"]:
                resultats = response.json()["results"]
                entreprises = [
                    {
                        "siren": resultat["siren"],
                        "denomination": resultat["nom_raison_sociale"]
                        or resultat["nom_complet"],
                        "activite": convertit_code_NAF(resultat["activite_principale"]),
                    }
                    for resultat in resultats
                ]
            else:
                nombre_resultats = 0
                entreprises = []
            return {
                "nombre_resultats": nombre_resultats,
                "entreprises": entreprises,
            }
        case 429:
            sentry_sdk.capture_message(TOO_MANY_REQUESTS_SENTRY_MESSAGE.format(NOM_API))
            raise TooManyRequestError(TOO_MANY_REQUESTS_ERROR)
        case 400:
            sentry_sdk.capture_message(INVALID_REQUEST_SENTRY_MESSAGE.format(NOM_API))
            raise APIError(SERVER_ERROR)
        case _:
            sentry_sdk.capture_message(API_ERROR_SENTRY_MESSAGE.format(NOM_API))
            raise ServerError(SERVER_ERROR)
