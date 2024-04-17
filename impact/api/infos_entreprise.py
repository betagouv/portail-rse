import api.recherche_entreprises
import api.sirene
from api.exceptions import APIError
from api.exceptions import SirenError


def infos_entreprise(siren):
    try:
        infos = api.recherche_entreprises.recherche(siren)
    except SirenError:
        raise
    except APIError:
        # utilise l'API Sirene en fallback
        infos = api.sirene.recherche_unite_legale(siren)
    return infos
