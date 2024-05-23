from datetime import date

import pytest

from entreprises.models import ActualisationCaracteristiquesAnnuelles
from entreprises.models import CaracteristiquesAnnuelles
from entreprises.models import Entreprise

CODE_SA = 5505
CODE_SA_COOPERATIVE = 5551
CODE_SAS = 5710
CODE_SCA = 5310
CODE_SE = 5800
CODE_AUTRE = 9240  # congrégation

CODE_PAYS_PORTUGAL = 99139
CODE_PAYS_CANADA = 99401


@pytest.fixture
def alice(django_user_model):
    alice = django_user_model.objects.create(
        prenom="Alice",
        nom="Cooper",
        email="alice@portail-rse.test",
        reception_actualites=False,
        is_email_confirmed=True,
    )
    return alice


@pytest.fixture
def bob(django_user_model):
    bob = django_user_model.objects.create(
        prenom="Bob",
        nom="Dylan",
        email="bob@portail-rse.test",
        reception_actualites=False,
        is_email_confirmed=True,
    )
    return bob


@pytest.fixture
def entreprise_non_qualifiee(alice):
    entreprise = Entreprise.objects.create(
        siren="000000001",
        denomination="Entreprise SAS",
        categorie_juridique_sirene=5710,
    )
    return entreprise


@pytest.fixture
def date_cloture_dernier_exercice():
    return date(2022, 12, 31)


@pytest.fixture
def entreprise_factory(db, date_cloture_dernier_exercice):
    def create_entreprise(
        siren="000000001",
        denomination="Entreprise SAS",
        categorie_juridique_sirene=CODE_SA,
        code_pays_etranger_sirene=None,
        code_NAF="01.11Z",
        date_cloture_exercice=date_cloture_dernier_exercice,
        date_derniere_qualification=None,
        est_cotee=False,
        est_interet_public=False,
        appartient_groupe=False,
        est_societe_mere=False,
        societe_mere_en_france=False,
        comptes_consolides=False,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        effectif_permanent=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        effectif_outre_mer=CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_MOINS_DE_250,
        effectif_groupe=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50,
        effectif_groupe_france=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50,
        effectif_groupe_permanent=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
        tranche_chiffre_affaires_consolide=CaracteristiquesAnnuelles.CA_MOINS_DE_60M,
        tranche_bilan_consolide=CaracteristiquesAnnuelles.BILAN_MOINS_DE_30M,
        bdese_accord=False,
        systeme_management_energie=False,
    ):
        entreprise = Entreprise.objects.create(
            siren=siren,
            denomination=denomination,
            date_cloture_exercice=date_cloture_exercice,
            date_derniere_qualification=date_derniere_qualification,
            categorie_juridique_sirene=categorie_juridique_sirene,
            code_pays_etranger_sirene=code_pays_etranger_sirene,
            code_NAF=code_NAF,
            est_cotee=est_cotee,
            est_interet_public=est_interet_public,
            appartient_groupe=appartient_groupe,
            est_societe_mere=est_societe_mere,
            societe_mere_en_france=societe_mere_en_france,
            comptes_consolides=comptes_consolides,
        )
        actualisation = ActualisationCaracteristiquesAnnuelles(
            date_cloture_exercice,
            effectif,
            effectif_permanent,
            effectif_outre_mer,
            effectif_groupe if appartient_groupe else None,
            effectif_groupe_france if appartient_groupe else None,
            effectif_groupe_permanent if appartient_groupe else None,
            tranche_chiffre_affaires,
            tranche_bilan,
            tranche_chiffre_affaires_consolide if comptes_consolides else None,
            tranche_bilan_consolide if comptes_consolides else None,
            bdese_accord,
            systeme_management_energie,
        )
        caracteristiques = entreprise.actualise_caracteristiques(actualisation)
        caracteristiques.save()
        return entreprise

    return create_entreprise
