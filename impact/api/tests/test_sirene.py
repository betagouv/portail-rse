import pytest

from api.sirene import recherche_unite_legale
from entreprises.models import CaracteristiquesAnnuelles


@pytest.mark.network
def test_api_fonctionnelle():
    SIREN = "130025265"
    infos = recherche_unite_legale(SIREN)

    assert infos == {
        "siren": SIREN,
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "denomination": "DIRECTION INTERMINISTERIELLE DU NUMERIQUE",
        "categorie_juridique_sirene": 7120,
        "code_pays_etranger_sirene": None,
    }
