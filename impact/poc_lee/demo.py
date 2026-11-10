from datetime import date

from entreprises.models import CaracteristiquesAnnuelles

DATE_CLOTURE = date(2025, 12, 31)
EMAIL = "demo-lee@portail-rse.test"

ENTREPRISES = [
    {
        "identifiant": "095680393",
        "denomination": "KEOLIS PAYS BASQUE",
        "code_NAF": "49.31Z",
        "code_postal": "64100",
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "effectif_securite_sociale": CaracteristiquesAnnuelles.EFFECTIF_SECURITE_SOCIALE_ENTRE_50_ET_249,
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_ENTRE_900K_ET_50M,
        "tranche_bilan": CaracteristiquesAnnuelles.BILAN_ENTRE_450K_ET_25M,
    },
    {
        "identifiant": "045850617",
        "denomination": "PRODUITS & COULEURS DU DOUAISIS",
        "code_NAF": "46.73B",
        "code_postal": "59500",
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        "effectif_securite_sociale": CaracteristiquesAnnuelles.EFFECTIF_SECURITE_SOCIALE_MOINS_DE_10,
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
        "tranche_bilan": CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
    },
]

SIRENS_DEMO = frozenset(e["identifiant"] for e in ENTREPRISES)
