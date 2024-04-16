from datetime import date

import requests

from entreprises.models import CaracteristiquesAnnuelles
from impact.settings import API_SIRENE_TOKEN


def recherche_unite_legale(siren):
    # documentation api sirene 3.11 https://www.sirene.fr/static-resources/htm/sommaire_311.html
    url = f"https://api.insee.fr/entreprises/sirene/V3.11/siren/{siren}?date={date.today().isoformat()}"
    response = requests.get(
        url, headers={"Authorization": f"Bearer {API_SIRENE_TOKEN}"}
    )

    data = response.json()["uniteLegale"]

    denomination = data["periodesUniteLegale"][0]["denominationUniteLegale"]
    categorie_juridique_sirene = int(
        data["periodesUniteLegale"][0]["categorieJuridiqueUniteLegale"]
    )
    tranche_effectif = int(data["trancheEffectifsUniteLegale"])
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

    return {
        "siren": siren,
        "effectif": effectif,
        "denomination": denomination,
        "categorie_juridique_sirene": categorie_juridique_sirene,
        "code_pays_etranger_sirene": None,
    }
