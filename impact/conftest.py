from datetime import date

import pytest

from entreprises.models import ActualisationCaracteristiquesAnnuelles
from entreprises.models import CaracteristiquesAnnuelles
from entreprises.models import Entreprise
from habilitations.models import Habilitation

CODE_SA = 5505
CODE_SA_COOPERATIVE = 5551
CODE_SAS = 5710
CODE_SCA = 5310
CODE_SE = 5800
CODE_AUTRE = 9240  # congrégation

CODE_PAYS_PORTUGAL = 99139
CODE_PAYS_CANADA = 99401

CODE_NAF_CEREALES = "01.11Z"


# Empêche tous les tests de faire des uploads de fichier en remplaçant le default storage par un InMemoryStorage
@pytest.fixture(autouse=True)
def use_in_memory_storage(settings):
    settings.STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.InMemoryStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }


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
        code_NAF="01.11Z",
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
        effectif_securite_sociale=CaracteristiquesAnnuelles.EFFECTIF_SECURITE_SOCIALE_MOINS_DE_10,
        effectif_outre_mer=CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_MOINS_DE_250,
        effectif_groupe=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50,
        effectif_groupe_france=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
        tranche_chiffre_affaires_consolide=CaracteristiquesAnnuelles.CA_MOINS_DE_60M,
        tranche_bilan_consolide=CaracteristiquesAnnuelles.BILAN_MOINS_DE_30M,
        bdese_accord=False,
        systeme_management_energie=False,
        utilisateur=None,
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
            effectif_securite_sociale,
            effectif_outre_mer,
            effectif_groupe if appartient_groupe else None,
            effectif_groupe_france if appartient_groupe else None,
            tranche_chiffre_affaires,
            tranche_bilan,
            tranche_chiffre_affaires_consolide if comptes_consolides else None,
            tranche_bilan_consolide if comptes_consolides else None,
            bdese_accord,
            systeme_management_energie,
        )
        caracteristiques = entreprise.actualise_caracteristiques(actualisation)
        caracteristiques.save()
        if utilisateur:
            Habilitation.ajouter(entreprise, utilisateur, fonctions="Président·e")
        return entreprise

    return create_entreprise


@pytest.fixture
def entreprise_unique_factory(entreprise_factory):
    counter = {"value": 2}

    def create_entreprise_with_unique_siren(**kwargs):
        if "siren" not in kwargs:
            kwargs["siren"] = f"{counter['value']:09d}"
            counter["value"] += 1
        return entreprise_factory(**kwargs)

    return create_entreprise_with_unique_siren


# the following fixtures were defined in `api.test.fixtures`,
# but they are used by several high-level packages
# (entreprise, reglementations, users ...), hence pulled-up.


@pytest.fixture
def mock_api_infos_entreprise(mocker):
    infos_entreprises_avec_donnees_financieres = {
        "siren": "000000001",
        "denomination": "Entreprise SAS",
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        "categorie_juridique_sirene": 5710,
        "code_pays_etranger_sirene": None,
        "code_NAF": "01.11Z",
        "date_cloture_exercice": date(2023, 12, 31),
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
        "tranche_chiffre_affaires_consolide": CaracteristiquesAnnuelles.CA_MOINS_DE_60M,
    }
    return mocker.patch(
        "api.infos_entreprise.infos_entreprise",
        return_value=infos_entreprises_avec_donnees_financieres,
    )


@pytest.fixture
def mock_api_recherche_par_nom_ou_siren(mocker):
    nombre_resultats = 3
    entreprises = [
        {
            "siren": "000000001",
            "denomination": "Entreprise Test 1",
            "activité": "Cultures non permanentes",
        },
        {
            "siren": "889297453",
            "denomination": "YAAL COOP",
            "activité": "Programmation, conseil et autres activités informatiques",
        },
        {
            "siren": "552032534",
            "denomination": "DANONE",
            "activité": "Activités des sièges sociaux",
        },
    ]
    return mocker.patch(
        "api.infos_entreprise.recherche_par_nom_ou_siren",
        return_value={"nombre_resultats": nombre_resultats, "entreprises": entreprises},
    )


@pytest.fixture
def mock_api_egapro(mocker):
    mocker.patch(
        "api.egapro.indicateurs_bdese",
        return_value={
            "nombre_femmes_plus_hautes_remunerations": None,
            "objectifs_progression": None,
        },
    )
    return mocker.patch(
        "api.egapro.is_index_egapro_published",
        return_value=False,
    )


@pytest.fixture
def mock_api_bges(mocker):
    return mocker.patch("api.bges.last_reporting_year", return_value=None)


@pytest.fixture
def mock_api_analyse_ia(mocker):
    return mocker.patch("api.analyse_ia.lancement_analyse", return_value="pending")
