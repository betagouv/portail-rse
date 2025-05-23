from datetime import date

import requests
import sentry_sdk
from django.conf import settings

from api.exceptions import API_ERROR_SENTRY_MESSAGE
from api.exceptions import APIError
from api.exceptions import SERVER_ERROR
from api.exceptions import ServerError
from api.exceptions import SIREN_NOT_FOUND_ERROR
from api.exceptions import SirenError
from api.exceptions import TOO_MANY_REQUESTS_ERROR
from api.exceptions import TOO_MANY_REQUESTS_SENTRY_MESSAGE
from api.exceptions import TooManyRequestError
from entreprises.models import CaracteristiquesAnnuelles
from utils.codes_naf import CODES_NAF

NOM_API = "sirene"
SIRENE_TIMEOUT = 3


def recherche_unite_legale_par_siren(siren):
    # documentation api sirene 3.11 https://www.sirene.fr/static-resources/documentation/sommaire_311.html
    url = f"https://api.insee.fr/api-sirene/3.11/siren/{siren}?date={date.today().isoformat()}"
    try:
        response = requests.get(
            url,
            headers={"X-INSEE-Api-Key-Integration": settings.API_SIRENE_KEY},
            timeout=SIRENE_TIMEOUT,
        )
    except Exception as e:
        with sentry_sdk.new_scope() as scope:
            scope.set_level("info")
            sentry_sdk.capture_exception(e)
        raise APIError(SERVER_ERROR)

    match response.status_code:
        case 200:
            data = response.json()["uniteLegale"]

            denomination = (
                data["periodesUniteLegale"][0]["denominationUniteLegale"]
                or data["periodesUniteLegale"][0]["nomUniteLegale"]
            )

            try:
                categorie_juridique_sirene = int(
                    data["periodesUniteLegale"][0]["categorieJuridiqueUniteLegale"]
                )
            except (ValueError, TypeError):
                sentry_sdk.capture_message(
                    "Catégorie juridique récupérée par l'API sirene invalide"
                )
                categorie_juridique_sirene = None

            effectif = convertit_tranche_effectif(data["trancheEffectifsUniteLegale"])
            code_NAF = (
                data["periodesUniteLegale"][0]["activitePrincipaleUniteLegale"] or None
            )

            # L'API sirene ne renseigne malheureusement pas le code pays étranger (bien récupéré par l'API recherche entreprises)
            # On souhaite être informé dès qu'il est manquant (utilisé dans la réglementation CSRD).
            # Il est toujours laissé vide actuellement (interprété comme France).
            # Il serait récupérable en utilisant le Nic du siège fourni par l'API. Cela permettrait
            # de construire le SIRET du siège. Une nouvelle requête POST sur https://api.insee.fr/entreprises/sirene/V3.11/siret
            # fournirait alors le code pays dans le champ codePaysEtrangerEtablissement.
            sentry_sdk.capture_message(
                f"Code pays étranger non récupéré par l'API {NOM_API}"
            )

            return {
                "siren": siren,
                "effectif": effectif,
                "denomination": denomination,
                "categorie_juridique_sirene": categorie_juridique_sirene,
                "code_pays_etranger_sirene": None,
                "code_NAF": code_NAF,
            }
        case 404:
            raise SirenError(SIREN_NOT_FOUND_ERROR)
        case 429:
            sentry_sdk.capture_message(TOO_MANY_REQUESTS_SENTRY_MESSAGE.format(NOM_API))
            raise TooManyRequestError(TOO_MANY_REQUESTS_ERROR)
        case _:
            sentry_sdk.capture_message(API_ERROR_SENTRY_MESSAGE.format(NOM_API))
            raise ServerError(SERVER_ERROR)


def convertit_tranche_effectif(tranche_effectif):
    # les tranches d'effectif correspondent à celles de l'API Sirene de l'Insee
    # https://www.sirene.fr/sirene/public/variable/tefen
    try:
        tranche_effectif = int(tranche_effectif)
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
    return effectif


def recherche_unites_legales_par_nom_ou_siren(recherche):
    url = "https://api.insee.fr/api-sirene/3.11/siren"
    params = {
        "q": f"periode(denominationUniteLegale:{recherche}) OR siren:{recherche}",
        "date": date.today().isoformat(),
        "champs": "siren,denominationUniteLegale,activitePrincipaleUniteLegale",
        "nombre": 5,
    }

    try:
        response = requests.get(
            url,
            params=params,
            headers={"X-INSEE-Api-Key-Integration": settings.API_SIRENE_KEY},
            timeout=SIRENE_TIMEOUT,
        )
    except Exception as e:
        with sentry_sdk.new_scope() as scope:
            scope.set_level("info")
            sentry_sdk.capture_exception(e)
        raise APIError(SERVER_ERROR)

    match response.status_code:
        case 200:
            nombre_resultats = response.json()["header"]["total"]
            resultats = response.json()["unitesLegales"]
            entreprises = [
                {
                    "siren": resultat["siren"],
                    "denomination": resultat["periodesUniteLegale"][0][
                        "denominationUniteLegale"
                    ],
                    "activite": convertit_code_NAF(
                        resultat["periodesUniteLegale"][0][
                            "activitePrincipaleUniteLegale"
                        ]
                    ),
                }
                for resultat in resultats
            ]
            return {
                "nombre_resultats": nombre_resultats,
                "entreprises": entreprises,
            }
        case 404:
            return {
                "nombre_resultats": 0,
                "entreprises": [],
            }
        case 429:
            sentry_sdk.capture_message(TOO_MANY_REQUESTS_SENTRY_MESSAGE.format(NOM_API))
            raise TooManyRequestError(TOO_MANY_REQUESTS_ERROR)
        case _:
            sentry_sdk.capture_message(API_ERROR_SENTRY_MESSAGE.format(NOM_API))
            raise ServerError(SERVER_ERROR)


def convertit_code_NAF(code_NAF):
    return CODES_NAF.get(code_NAF[:4], "")
