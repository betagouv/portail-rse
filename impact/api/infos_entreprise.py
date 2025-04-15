import api.ratios_financiers
import api.recherche_entreprises
import api.sirene
from api.exceptions import APIError
from api.exceptions import SirenError


def infos_entreprise(siren, donnees_financieres=False):
    try:
        infos = api.recherche_entreprises.recherche_par_siren(siren)
    except SirenError:
        raise
    except APIError:
        # utilise l'API Sirene en fallback
        infos = api.sirene.recherche_unite_legale(siren)

    if donnees_financieres:
        try:
            infos.update(api.ratios_financiers.dernier_exercice_comptable(siren))
        except APIError:
            infos.update(api.ratios_financiers.dernier_exercice_comptable_vide())
    return infos


def recherche_par_nom_ou_siren(recherche):
    # TODO: ajouter un fallback sur l'API Sirene
    entreprises = api.recherche_entreprises.recherche_textuelle(recherche)
    return entreprises
