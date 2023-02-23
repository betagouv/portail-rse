import requests

from .exceptions import APIError

def recherche(siren):
    # documentation api recherche d'entreprises 1.0.0 https://api.gouv.fr/documentation/api-recherche-entreprises
    url = f"https://recherche-entreprises.api.gouv.fr/search?q={siren}&page=1&per_page=1"
    response = requests.get(url)
    if response.status_code == 200 and response.json()["total_results"]:
        data = response.json()["results"][0]
        raison_sociale = data["nom_raison_sociale"]
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
            "raison_sociale": raison_sociale,
        }
    else:
        raise APIError()