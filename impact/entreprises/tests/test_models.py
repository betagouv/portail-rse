from datetime import date
from datetime import datetime
from datetime import timedelta
from datetime import timezone

import pytest
from django.db import IntegrityError
from freezegun import freeze_time

from conftest import CODE_AUTRE
from conftest import CODE_PAYS_CANADA
from conftest import CODE_PAYS_PORTUGAL
from entreprises.models import ActualisationCaracteristiquesAnnuelles
from entreprises.models import CaracteristiquesAnnuelles
from entreprises.models import CategorieJuridique
from entreprises.models import convertit_categorie_juridique
from entreprises.models import convertit_code_NAF
from entreprises.models import convertit_code_pays
from entreprises.models import Entreprise
from entreprises.models import est_dans_EEE
from habilitations.enums import UserRole
from habilitations.models import Habilitation


@pytest.mark.django_db(transaction=True)
def test_entreprise():
    now = datetime(2023, 1, 27, 16, 1, tzinfo=timezone.utc)

    with freeze_time(now):
        entreprise = Entreprise.objects.create(
            siren="123456789",
            denomination="Entreprise SAS",
            date_cloture_exercice=date(2023, 7, 7),
            appartient_groupe=False,
            comptes_consolides=False,
        )

    assert entreprise.created_at == now
    assert entreprise.updated_at == now
    assert entreprise.siren == "123456789"
    assert entreprise.denomination == "Entreprise SAS"
    assert entreprise.date_cloture_exercice == date(2023, 7, 7)
    assert entreprise.appartient_groupe is False
    assert entreprise.comptes_consolides is False
    assert not entreprise.users.all()

    with pytest.raises(IntegrityError):
        Entreprise.objects.create(
            siren="123456789", denomination="Autre Entreprise SAS"
        )

    with freeze_time(now + timedelta(1)):
        entreprise.denomination = "Nouveau nom SAS"
        entreprise.save()

    assert entreprise.updated_at == now + timedelta(1)


def test_caracteristiques_sont_qualifiantes_avec_groupe(
    entreprise_non_qualifiee,
):
    entreprise_non_qualifiee.est_cotee = False
    entreprise_non_qualifiee.est_interet_public = False
    entreprise_non_qualifiee.appartient_groupe = None
    entreprise_non_qualifiee.est_societe_mere = None
    entreprise_non_qualifiee.societe_mere_en_france = None
    entreprise_non_qualifiee.comptes_consolides = None
    entreprise_non_qualifiee.code_NAF = None

    caracteristiques = CaracteristiquesAnnuelles(
        entreprise=entreprise_non_qualifiee,
        date_cloture_exercice=date(2023, 7, 7),
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        effectif_securite_sociale=CaracteristiquesAnnuelles.EFFECTIF_SECURITE_SOCIALE_MOINS_DE_10,
        effectif_outre_mer=CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_MOINS_DE_250,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
        bdese_accord=True,
        systeme_management_energie=True,
    )

    assert not caracteristiques.groupe_est_qualifie
    assert not caracteristiques.sont_qualifiantes

    entreprise_non_qualifiee.appartient_groupe = True

    assert not caracteristiques.groupe_est_qualifie
    assert not caracteristiques.sont_qualifiantes

    entreprise_non_qualifiee.comptes_consolides = False

    assert not caracteristiques.groupe_est_qualifie
    assert not caracteristiques.sont_qualifiantes

    entreprise_non_qualifiee.societe_mere_en_france = False

    assert not caracteristiques.groupe_est_qualifie
    assert not caracteristiques.sont_qualifiantes

    caracteristiques.effectif_groupe = CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS

    assert not caracteristiques.groupe_est_qualifie
    assert not caracteristiques.sont_qualifiantes

    caracteristiques.effectif_groupe_france = (
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS
    )

    assert not caracteristiques.groupe_est_qualifie
    assert not caracteristiques.sont_qualifiantes

    entreprise_non_qualifiee.est_societe_mere = False

    assert caracteristiques.groupe_est_qualifie
    assert not caracteristiques.sont_qualifiantes

    entreprise_non_qualifiee.comptes_consolides = True

    assert not caracteristiques.groupe_est_qualifie
    assert not caracteristiques.sont_qualifiantes

    caracteristiques.tranche_chiffre_affaires_consolide = (
        CaracteristiquesAnnuelles.CA_MOINS_DE_60M
    )
    caracteristiques.tranche_bilan_consolide = (
        CaracteristiquesAnnuelles.BILAN_MOINS_DE_30M
    )

    assert caracteristiques.groupe_est_qualifie
    assert not caracteristiques.sont_qualifiantes

    entreprise_non_qualifiee.code_NAF = "11.11Z"

    assert caracteristiques.groupe_est_qualifie
    assert caracteristiques.sont_qualifiantes

    with freeze_time("2024-11-14"):
        # la date de dernière modification avant la date de "requalification" :
        # les caractéristiques ne doivent pas être qualifiantes.
        entreprise_non_qualifiee.save()

        assert (
            not caracteristiques.sont_qualifiantes
        ), "non qualifiée : MaJ de l'entreprise antérieure à la date de requalification"


def test_caracteristiques_sont_qualifiantes_sans_groupe(
    entreprise_non_qualifiee,
):
    entreprise_non_qualifiee.appartient_groupe = False
    entreprise_non_qualifiee.code_NAF = None

    caracteristiques = CaracteristiquesAnnuelles(
        entreprise=entreprise_non_qualifiee,
    )

    assert not caracteristiques.sont_qualifiantes

    entreprise_non_qualifiee.est_cotee = False

    assert not caracteristiques.sont_qualifiantes

    entreprise_non_qualifiee.est_interet_public = False

    assert not caracteristiques.sont_qualifiantes

    caracteristiques.date_cloture_exercice = date(2023, 7, 7)

    assert not caracteristiques.sont_qualifiantes

    caracteristiques.effectif = CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10

    assert not caracteristiques.sont_qualifiantes

    caracteristiques.effectif_securite_sociale = (
        CaracteristiquesAnnuelles.EFFECTIF_SECURITE_SOCIALE_MOINS_DE_10
    )

    assert not caracteristiques.sont_qualifiantes

    caracteristiques.effectif_outre_mer = (
        CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_MOINS_DE_250
    )

    assert not caracteristiques.sont_qualifiantes

    caracteristiques.tranche_chiffre_affaires = (
        CaracteristiquesAnnuelles.CA_MOINS_DE_900K
    )

    assert not caracteristiques.sont_qualifiantes

    caracteristiques.tranche_bilan = CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K

    assert not caracteristiques.sont_qualifiantes

    caracteristiques.bdese_accord = True

    assert not caracteristiques.sont_qualifiantes

    caracteristiques.systeme_management_energie = True

    assert not caracteristiques.sont_qualifiantes

    entreprise_non_qualifiee.code_NAF = "11.11Z"

    assert caracteristiques.sont_qualifiantes

    with freeze_time("2024-11-14"):
        # la date de dernière modification avant la date de "requalification" :
        # les caractéristiques ne doivent pas être qualifiantes.
        entreprise_non_qualifiee.save()

        assert (
            not caracteristiques.sont_qualifiantes
        ), "non qualifiée : MaJ de l'entreprise antérieure à la date de requalification"


@pytest.mark.django_db(transaction=True)
def test_dernieres_caracteristiques_qualifiantes(entreprise_non_qualifiee):
    assert entreprise_non_qualifiee.dernieres_caracteristiques_qualifiantes is None

    entreprise_non_qualifiee.est_cotee = False
    entreprise_non_qualifiee.est_interet_public = False
    entreprise_non_qualifiee.appartient_groupe = False
    entreprise_non_qualifiee.comptes_consolides = False
    entreprise_non_qualifiee.save()
    actualisation = ActualisationCaracteristiquesAnnuelles(
        date_cloture_exercice=date(2023, 7, 7),
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        effectif_securite_sociale=CaracteristiquesAnnuelles.EFFECTIF_SECURITE_SOCIALE_MOINS_DE_10,
        effectif_outre_mer=CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_MOINS_DE_250,
        effectif_groupe=None,
        effectif_groupe_france=None,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
        tranche_chiffre_affaires_consolide=None,
        tranche_bilan_consolide=None,
        bdese_accord=True,
        systeme_management_energie=True,
    )
    caracteristiques_2023 = entreprise_non_qualifiee.actualise_caracteristiques(
        actualisation
    )
    caracteristiques_2023.save()

    with freeze_time(date(2025, 1, 27)):
        assert (
            entreprise_non_qualifiee.dernieres_caracteristiques_qualifiantes
            == caracteristiques_2023
        )

    caracteristiques_2024 = CaracteristiquesAnnuelles(
        annee=2024,
        entreprise=entreprise_non_qualifiee,
    )
    caracteristiques_2024.save()

    with freeze_time(date(2025, 1, 27)):
        assert (
            entreprise_non_qualifiee.dernieres_caracteristiques_qualifiantes
            == caracteristiques_2023
        )


def test_actualise_caracteristiques(entreprise_non_qualifiee):
    assert entreprise_non_qualifiee.caracteristiques_actuelles() is None

    effectif = CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499
    effectif_securite_sociale = (
        CaracteristiquesAnnuelles.EFFECTIF_SECURITE_SOCIALE_MOINS_DE_10
    )
    effectif_outre_mer = CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_MOINS_DE_250
    effectif_groupe = CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS
    effectif_groupe_france = CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS
    tranche_chiffre_affaires = CaracteristiquesAnnuelles.CA_MOINS_DE_900K
    tranche_bilan = CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K
    tranche_chiffre_affaires_consolide = CaracteristiquesAnnuelles.CA_MOINS_DE_60M
    tranche_bilan_consolide = CaracteristiquesAnnuelles.BILAN_MOINS_DE_30M
    bdese_accord = False
    systeme_management_energie = False
    date_cloture_exercice = date(2023, 7, 7)

    actualisation = ActualisationCaracteristiquesAnnuelles(
        date_cloture_exercice,
        effectif,
        effectif_securite_sociale,
        effectif_outre_mer,
        effectif_groupe,
        effectif_groupe_france,
        tranche_chiffre_affaires,
        tranche_bilan,
        tranche_chiffre_affaires_consolide,
        tranche_bilan_consolide,
        bdese_accord,
        systeme_management_energie,
    )
    caracteristiques = entreprise_non_qualifiee.actualise_caracteristiques(
        actualisation
    )
    caracteristiques.save()

    caracteristiques = CaracteristiquesAnnuelles.objects.get(pk=caracteristiques.pk)
    assert caracteristiques.entreprise == entreprise_non_qualifiee
    assert caracteristiques.annee == 2023
    assert caracteristiques.effectif == effectif
    assert caracteristiques.effectif_securite_sociale == effectif_securite_sociale
    assert caracteristiques.effectif_outre_mer == effectif_outre_mer
    assert caracteristiques.effectif_groupe == effectif_groupe
    assert caracteristiques.effectif_groupe_france == effectif_groupe_france
    assert caracteristiques.tranche_chiffre_affaires == tranche_chiffre_affaires
    assert caracteristiques.tranche_bilan == tranche_bilan
    assert (
        caracteristiques.tranche_chiffre_affaires_consolide
        == tranche_chiffre_affaires_consolide
    )
    assert caracteristiques.tranche_bilan_consolide == tranche_bilan_consolide
    assert caracteristiques.bdese_accord == bdese_accord
    assert caracteristiques.systeme_management_energie == systeme_management_energie
    entreprise_non_qualifiee.refresh_from_db()
    assert entreprise_non_qualifiee.caracteristiques_annuelles(2023) == caracteristiques

    nouvel_effectif = CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999
    nouvel_effectif_securite_sociale = (
        CaracteristiquesAnnuelles.EFFECTIF_SECURITE_SOCIALE_500_ET_PLUS
    )
    nouvel_effectif_outre_mer = CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_250_ET_PLUS
    nouvel_effectif_groupe = CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999
    nouvel_effectif_groupe_international = (
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999
    )
    nouvelle_tranche_chiffre_affaires = CaracteristiquesAnnuelles.CA_ENTRE_900K_ET_50M
    nouvelle_tranche_bilan = CaracteristiquesAnnuelles.BILAN_ENTRE_25M_ET_43M
    nouvelle_tranche_chiffre_affaires_consolide = (
        CaracteristiquesAnnuelles.CA_100M_ET_PLUS
    )
    nouvelle_tranche_bilan_consolide = CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS
    nouveau_bdese_accord = True
    nouveau_systeme_management_energie = True

    actualisation = ActualisationCaracteristiquesAnnuelles(
        date_cloture_exercice,
        nouvel_effectif,
        nouvel_effectif_securite_sociale,
        nouvel_effectif_outre_mer,
        nouvel_effectif_groupe,
        nouvel_effectif_groupe_international,
        nouvelle_tranche_chiffre_affaires,
        nouvelle_tranche_bilan,
        nouvelle_tranche_chiffre_affaires_consolide,
        nouvelle_tranche_bilan_consolide,
        nouveau_bdese_accord,
        nouveau_systeme_management_energie,
    )
    nouvelles_caracteristiques = entreprise_non_qualifiee.actualise_caracteristiques(
        actualisation
    )
    nouvelles_caracteristiques.save()

    nouvelles_caracteristiques = CaracteristiquesAnnuelles.objects.get(
        pk=nouvelles_caracteristiques.pk
    )
    assert nouvelles_caracteristiques.entreprise == entreprise_non_qualifiee
    assert nouvelles_caracteristiques.annee == 2023
    assert nouvelles_caracteristiques.effectif == nouvel_effectif
    assert (
        nouvelles_caracteristiques.effectif_securite_sociale
        == nouvel_effectif_securite_sociale
    )
    assert nouvelles_caracteristiques.effectif_outre_mer == nouvel_effectif_outre_mer
    assert nouvelles_caracteristiques.effectif_groupe == nouvel_effectif_groupe
    assert (
        nouvelles_caracteristiques.effectif_groupe_france
        == nouvel_effectif_groupe_international
    )
    assert (
        nouvelles_caracteristiques.tranche_chiffre_affaires
        == nouvelle_tranche_chiffre_affaires
    )
    assert nouvelles_caracteristiques.tranche_bilan == nouvelle_tranche_bilan
    assert (
        nouvelles_caracteristiques.tranche_chiffre_affaires_consolide
        == nouvelle_tranche_chiffre_affaires_consolide
    )
    assert (
        nouvelles_caracteristiques.tranche_bilan_consolide
        == nouvelle_tranche_bilan_consolide
    )
    assert nouvelles_caracteristiques.bdese_accord == nouveau_bdese_accord
    assert (
        nouvelles_caracteristiques.systeme_management_energie
        == nouveau_systeme_management_energie
    )
    entreprise_non_qualifiee.refresh_from_db()
    assert (
        entreprise_non_qualifiee.caracteristiques_annuelles(2023)
        == nouvelles_caracteristiques
    )


def test_actualise_caracteristiques_conserve_attributs_entreprise_non_commités(
    entreprise_factory,
):
    entreprise = entreprise_factory(appartient_groupe=False)
    entreprise.appartient_groupe = True
    # ne commit pas

    actualisation = ActualisationCaracteristiquesAnnuelles(
        date_cloture_exercice=entreprise.date_cloture_exercice,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        effectif_securite_sociale=CaracteristiquesAnnuelles.EFFECTIF_SECURITE_SOCIALE_MOINS_DE_10,
        effectif_outre_mer=CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_MOINS_DE_250,
        effectif_groupe=CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        effectif_groupe_france=CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
        tranche_chiffre_affaires_consolide=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
        tranche_bilan_consolide=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        bdese_accord=False,
        systeme_management_energie=False,
    )
    caracteristiques = entreprise.actualise_caracteristiques(actualisation)

    assert entreprise.appartient_groupe
    assert caracteristiques.entreprise == entreprise
    assert caracteristiques.entreprise.appartient_groupe
    entreprise_en_base = Entreprise.objects.get(pk=entreprise.id)
    assert not entreprise_en_base.appartient_groupe
    caracteristiques_en_base = CaracteristiquesAnnuelles.objects.get(
        entreprise=entreprise_en_base
    )
    assert not caracteristiques_en_base.entreprise.appartient_groupe

    entreprise.save()
    caracteristiques.save()

    entreprise_en_base = Entreprise.objects.get(pk=entreprise.id)
    assert entreprise_en_base.appartient_groupe
    caracteristiques_en_base = CaracteristiquesAnnuelles.objects.get(
        entreprise=entreprise_en_base
    )
    assert caracteristiques_en_base.entreprise.appartient_groupe


@pytest.mark.django_db(transaction=True)
def test_caracteristiques_annuelles(entreprise_non_qualifiee):
    with pytest.raises(IntegrityError):
        CaracteristiquesAnnuelles.objects.create(annee=2023)

    CaracteristiquesAnnuelles.objects.create(
        entreprise=entreprise_non_qualifiee, annee=2023
    )


def test_uniques_caracteristiques_annuelles(entreprise_non_qualifiee):
    caracteristiques = CaracteristiquesAnnuelles(
        entreprise=entreprise_non_qualifiee, annee=2023
    )
    caracteristiques.save()

    with pytest.raises(IntegrityError):
        caracteristiques_bis = CaracteristiquesAnnuelles(
            entreprise=entreprise_non_qualifiee, annee=2023
        )
        caracteristiques_bis.save()


def test_caracteristiques_actuelles_selon_la_date_de_cloture(entreprise_non_qualifiee):
    entreprise_non_qualifiee.date_cloture_exercice = date(2000, 6, 30)
    for annee in (2022, 2023):
        actualisation = ActualisationCaracteristiquesAnnuelles(
            date(annee, 6, 30),
            effectif=CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
            effectif_securite_sociale=None,
            effectif_outre_mer=CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_250_ET_PLUS,
            effectif_groupe=None,
            effectif_groupe_france=None,
            tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
            tranche_bilan=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
            tranche_chiffre_affaires_consolide=None,
            tranche_bilan_consolide=None,
            bdese_accord=False,
            systeme_management_energie=False,
        )
        caracs = entreprise_non_qualifiee.actualise_caracteristiques(actualisation)
        caracs.save()

    with freeze_time(datetime(2023, 1, 27, 16, 1, tzinfo=timezone.utc)):
        assert entreprise_non_qualifiee.caracteristiques_actuelles().annee == 2022

    with freeze_time(datetime(2023, 11, 27, 16, 1, tzinfo=timezone.utc)):
        assert entreprise_non_qualifiee.caracteristiques_actuelles().annee == 2023

    with freeze_time(datetime(2024, 11, 27, 16, 1, tzinfo=timezone.utc)):
        assert entreprise_non_qualifiee.caracteristiques_actuelles() is None


def test_caracteristiques_actuelles_annee_bissextile(entreprise_factory):
    entreprise = entreprise_factory(date_cloture_exercice=date(2024, 2, 29))

    with freeze_time(datetime(2025, 1, 27, 16, 1, tzinfo=timezone.utc)):
        assert entreprise.caracteristiques_actuelles().annee == 2024


def test_categorie_SA():
    PLAGES = [
        range(
            5505,  # SA à participation ouvrière à conseil d'administration
            5515 + 1,  # SA nationale à conseil d’administration
        ),
        range(
            5522,  # SA immobilière pour le commerce et l'industrie (SICOMI) à conseil d'administration
            5542 + 1,  # SA d'attribution à conseil d'administration
        ),
        range(
            5599,  # SA à conseil d'administration (s.a.i.)
            5642 + 1,  # SA d'attribution à directoire
        ),
        range(
            5670,  # Société de Participations Financières de Profession Libérale Société anonyme à Directoire (SPFPL SA à directoire)
            5699 + 1,  # SA à directoire (s.a.i.)
        ),
    ]

    for plage in PLAGES:
        for categorie_juridique_sirene in plage:
            categorie_juridique = convertit_categorie_juridique(
                categorie_juridique_sirene
            )

            assert categorie_juridique == CategorieJuridique.SOCIETE_ANONYME
            assert categorie_juridique.label == "Société Anonyme"

    for entre_plage in (5543, 5643, 5700):
        categorie_juridique = convertit_categorie_juridique(entre_plage)

        assert categorie_juridique != CategorieJuridique.SOCIETE_ANONYME

    for categorie_juridique_sirene in (
        5546,  # SA de HLM à conseil d'administration
        5646,  # SA de HLM à directoire
        5648,  # SA de crédit immobilier à directoire
    ):
        categorie_juridique = convertit_categorie_juridique(categorie_juridique_sirene)

        assert categorie_juridique == CategorieJuridique.SOCIETE_ANONYME
        assert categorie_juridique.label == "Société Anonyme"


def test_categorie_SCA():
    for categorie_juridique_sirene in (
        5308,  # Société en commandite par actions
        5385,  # Société d'exercice libéral en commandite par actions
    ):
        categorie_juridique = convertit_categorie_juridique(categorie_juridique_sirene)

        assert categorie_juridique == CategorieJuridique.SOCIETE_COMMANDITE_PAR_ACTIONS
        assert categorie_juridique.label == "Société en Commandite par Actions"


def test_categorie_SAS():
    for categorie_juridique_sirene in (
        5710,  # SAS, société par actions simplifiée
        5785,  # Société d'exercice libéral par action simplifiée
    ):
        categorie_juridique = convertit_categorie_juridique(categorie_juridique_sirene)

        assert categorie_juridique == CategorieJuridique.SOCIETE_PAR_ACTIONS_SIMPLIFIEES
        assert categorie_juridique.label == "Société par Actions Simplifiées"


def test_categorie_SE():
    categorie_juridique = convertit_categorie_juridique(5800)

    assert categorie_juridique == CategorieJuridique.SOCIETE_EUROPEENNE
    assert categorie_juridique.label == "Société Européenne"


def test_categorie_Societe_Cooperative_Agricole():
    for categorie_juridique_sirene in (6317, 6318):
        categorie_juridique = convertit_categorie_juridique(categorie_juridique_sirene)

        assert categorie_juridique == CategorieJuridique.SOCIETE_COOPERATIVE_AGRICOLE
        assert categorie_juridique.label == "Société Coopérative Agricole"


def test_categorie_societe_cooperative():
    PLAGES = [
        range(
            5443,  # SARL coopérative de construction
            5460 + 1,  # Autre SARL coopérative
        ),
        range(
            5551,  # SA coopérative de consommation à conseil d'administration
            5560 + 1,  # Autre SA coopérative à conseil d'administration
        ),
        range(
            5651,  # SA coopérative de consommation à directoire
            5660 + 1,  # Autre SA coopérative à directoire
        ),
    ]

    for plage in PLAGES:
        for categorie_juridique_sirene in plage:
            categorie_juridique = convertit_categorie_juridique(
                categorie_juridique_sirene
            )

            assert (
                categorie_juridique
                == CategorieJuridique.SOCIETE_COOPERATIVE_DE_PRODUCTION
            )
            assert categorie_juridique.label == "Société Coopérative de Production"

    for entre_plage in (5461, 5561, 5661):
        categorie_juridique = convertit_categorie_juridique(entre_plage)

        assert (
            categorie_juridique != CategorieJuridique.SOCIETE_COOPERATIVE_DE_PRODUCTION
        )

    for categorie_juridique_sirene in (
        5543,  # SA coopérative de construction à conseil d'administration
        5547,  # SA coopérative de production de HLM à conseil d'administration
        5643,  # SA coopérative de construction à directoire
        5647,  # Société coopérative de production de HLM anonyme à directoire
    ):
        categorie_juridique = convertit_categorie_juridique(categorie_juridique_sirene)

        assert (
            categorie_juridique == CategorieJuridique.SOCIETE_COOPERATIVE_DE_PRODUCTION
        )
        assert categorie_juridique.label == "Société Coopérative de Production"


def test_categorie_assurance_a_forme_mutuelle():
    categorie_juridique = convertit_categorie_juridique(6411)

    assert categorie_juridique == CategorieJuridique.SOCIETE_ASSURANCE_MUTUELLE
    assert categorie_juridique.label == "Société d'assurance à forme mutuelle"


def test_categorie_Mutuelle():
    categorie_juridique = convertit_categorie_juridique(8210)

    assert categorie_juridique == CategorieJuridique.MUTUELLE
    assert categorie_juridique.label == "Mutuelle"


def test_categorie_Institution_Prevoyance():
    categorie_juridique = convertit_categorie_juridique(8510)

    assert categorie_juridique == CategorieJuridique.INSTITUTION_PREVOYANCE
    assert categorie_juridique.label == "Institution de Prévoyance"


def test_categorie_autre():
    categorie_juridique_sirene = CODE_AUTRE
    categorie_juridique = convertit_categorie_juridique(categorie_juridique_sirene)

    assert categorie_juridique == CategorieJuridique.AUTRE
    assert categorie_juridique.label == ""


def test_aucune_categorie():
    categorie_juridique_sirene = None
    assert convertit_categorie_juridique(categorie_juridique_sirene) is None


def test_societe_cooperative_est_une_SA():
    PLAGES = [
        range(
            5551,  # SA coopérative de consommation à conseil d'administration
            5560 + 1,  # Autre SA coopérative à conseil d'administration
        ),
        range(
            5651,  # SA coopérative de consommation à directoire
            5660 + 1,  # Autre SA coopérative à directoire
        ),
    ]

    for plage in PLAGES:
        for categorie_juridique_sirene in plage:
            assert CategorieJuridique.est_une_SA_cooperative(categorie_juridique_sirene)

    for categorie_juridique_sirene in range(
        5443,  # SARL coopérative de construction
        5460 + 1,  # Autre SARL coopérative
    ):
        assert not CategorieJuridique.est_une_SA_cooperative(categorie_juridique_sirene)

    for categorie_juridique_sirene in (
        5543,  # SA coopérative de construction à conseil d'administration
        5547,  # SA coopérative de production de HLM à conseil d'administration
        5643,  # SA coopérative de construction à directoire
        5647,  # Société Coopérative de HLM anonyme à directoire
    ):
        assert CategorieJuridique.est_une_SA_cooperative(categorie_juridique_sirene)


def test_est_une_SA_cooperative_sans_categorie_juridique_sirene():
    assert CategorieJuridique.est_une_SA_cooperative(None) is None


def test_est_dans_EEE():
    CODES_PAYS_ETRANGERS = [
        99109,  # Allemagne
        99110,  # Autriche
        99131,  # Belgique
        99111,  # Bulgarie
        99254,  # Chypre
        99119,  # Croatie
        99101,  # Danemark
        99134,  # Espagne
        99106,  # Estonie
        99105,  # Finlande
        None,  # France
        99126,  # Grèce
        99112,  # Hongrie
        99136,  # Irlande
        99102,  # Islande
        99127,  # Italie
        99107,  # Lettonie
        99113,  # Liechtenstein
        99108,  # Lituanie
        99137,  # Luxembourg
        99144,  # Malte
        99103,  # Norvège
        99135,  # Pays-Bas
        99122,  # Pologne
        99139,  # Portugal
        99116,  # République tchèque
        99114,  # Roumanie
        99117,  # Slovaquie
        99145,  # Slovénie
        99104,  # Suède
    ]

    for code_pays_etranger in CODES_PAYS_ETRANGERS:
        assert est_dans_EEE(code_pays_etranger)

    CODES_PAYS_ETRANGERS = [
        99212,  # Afghanistan
        99350,  # Maroc
        99401,  # Canada
    ]

    for code_pays_etranger in CODES_PAYS_ETRANGERS:
        assert not est_dans_EEE(code_pays_etranger)


def test_convertit_code_pays():
    assert convertit_code_pays(CODE_PAYS_CANADA) == "Canada"
    assert convertit_code_pays(CODE_PAYS_PORTUGAL) == "Portugal"
    assert convertit_code_pays(None) == "France"
    assert convertit_code_pays(11111) is None  # code inexistant actuellement


def test_exercice_comptable_est_annee_civile():
    caracteristiques = CaracteristiquesAnnuelles(
        date_cloture_exercice=date(2023, 7, 7),
    )
    assert not caracteristiques.exercice_comptable_est_annee_civile

    caracteristiques = CaracteristiquesAnnuelles(
        date_cloture_exercice=date(2023, 12, 31),
    )
    assert caracteristiques.exercice_comptable_est_annee_civile


@pytest.mark.django_db(transaction=True)
def test_secteur_principal_d_une_entreprise():
    entreprise = Entreprise.objects.create(
        code_NAF="01.11Z",
        siren="111111111",
    )

    assert entreprise.secteur_principal == "01.1 - Cultures non permanentes"


@pytest.mark.django_db(transaction=True)
def test_secteur_principal_d_une_entreprise_sans_code_NAF_valide():
    entreprise = Entreprise.objects.create(
        code_NAF=None,
        siren="111111111",
    )

    assert entreprise.secteur_principal is None


def test_convertit_code_NAF():
    assert convertit_code_NAF("01.11Z") == {
        "code": "01.1",
        "label": "Cultures non permanentes",
    }
    assert convertit_code_NAF("01.21") == {
        "code": "01.2",
        "label": "Cultures permanentes",
    }


def test_convertit_code_NAF_sans_correspondance():
    assert convertit_code_NAF(None) is None
    assert convertit_code_NAF("yolo") is None


# Tests pour la propriété a_proprietaire_non_conseiller


@pytest.fixture
def conseiller_rse(django_user_model):
    return django_user_model.objects.create(
        prenom="Claire",
        nom="Conseillère",
        email="claire@conseil-rse.test",
        is_email_confirmed=True,
        is_conseiller_rse=True,
    )


@pytest.mark.django_db
def test_entreprise_sans_habilitation_na_pas_de_proprietaire_non_conseiller(
    entreprise_factory,
):
    """Une entreprise sans aucune habilitation n'a pas de propriétaire non conseiller."""
    entreprise = entreprise_factory()

    assert not entreprise.a_proprietaire_non_conseiller


@pytest.mark.django_db
def test_entreprise_avec_proprietaire_standard(alice, entreprise_factory):
    """Une entreprise avec un propriétaire standard a un propriétaire non conseiller."""
    entreprise = entreprise_factory()
    Habilitation.ajouter(entreprise, alice, UserRole.PROPRIETAIRE)

    assert entreprise.a_proprietaire_non_conseiller


@pytest.mark.django_db
def test_entreprise_avec_uniquement_conseiller_rse(conseiller_rse, entreprise_factory):
    """Une entreprise avec uniquement un conseiller RSE n'a pas de propriétaire non conseiller."""
    entreprise = entreprise_factory()
    Habilitation.ajouter(entreprise, conseiller_rse, UserRole.EDITEUR)

    assert not entreprise.a_proprietaire_non_conseiller


@pytest.mark.django_db
def test_entreprise_avec_conseiller_et_proprietaire_standard(
    alice, conseiller_rse, entreprise_factory
):
    """Une entreprise avec un conseiller RSE et un propriétaire standard a un propriétaire non conseiller."""
    entreprise = entreprise_factory()
    Habilitation.ajouter(entreprise, alice, UserRole.PROPRIETAIRE)
    Habilitation.ajouter(entreprise, conseiller_rse, UserRole.EDITEUR)

    assert entreprise.a_proprietaire_non_conseiller


@pytest.mark.django_db
def test_entreprise_avec_editeur_standard_na_pas_de_proprietaire_non_conseiller(
    alice, entreprise_factory
):
    """Une entreprise avec uniquement un éditeur standard n'a pas de propriétaire non conseiller."""
    entreprise = entreprise_factory()
    Habilitation.ajouter(entreprise, alice, UserRole.EDITEUR)

    assert not entreprise.a_proprietaire_non_conseiller


# Tests pour la propriété est_structure_vacante

from invitations.models import Invitation


@pytest.mark.django_db
def test_structure_vacante_avec_invitation_proprietaire_tiers(
    conseiller_rse, entreprise_factory
):
    """Une structure est vacante si elle a une invitation propriétaire tiers en attente."""
    entreprise = entreprise_factory()
    Habilitation.ajouter(entreprise, conseiller_rse, UserRole.EDITEUR)
    Invitation.objects.create(
        entreprise=entreprise,
        email="futur@proprietaire.test",
        role=UserRole.PROPRIETAIRE,
        inviteur=conseiller_rse,
        est_invitation_proprietaire_tiers=True,
    )

    assert entreprise.est_structure_vacante


@pytest.mark.django_db
def test_structure_non_vacante_avec_proprietaire_valide(
    alice, conseiller_rse, entreprise_factory
):
    """Une structure n'est pas vacante si elle a un propriétaire validé."""
    entreprise = entreprise_factory()
    Habilitation.ajouter(entreprise, alice, UserRole.PROPRIETAIRE)
    Habilitation.ajouter(entreprise, conseiller_rse, UserRole.EDITEUR)
    Invitation.objects.create(
        entreprise=entreprise,
        email="autre@proprietaire.test",
        role=UserRole.PROPRIETAIRE,
        inviteur=conseiller_rse,
        est_invitation_proprietaire_tiers=True,
    )

    assert not entreprise.est_structure_vacante


@pytest.mark.django_db
def test_structure_non_vacante_sans_invitation_proprietaire_tiers(
    conseiller_rse, entreprise_factory
):
    """Une structure n'est pas vacante si elle n'a pas d'invitation propriétaire tiers."""
    entreprise = entreprise_factory()
    Habilitation.ajouter(entreprise, conseiller_rse, UserRole.EDITEUR)
    # Pas d'invitation

    assert not entreprise.est_structure_vacante


@pytest.mark.django_db
def test_structure_non_vacante_invitation_acceptee(
    alice, conseiller_rse, entreprise_factory
):
    """Une structure n'est pas vacante si l'invitation a été acceptée."""
    entreprise = entreprise_factory()
    Habilitation.ajouter(entreprise, conseiller_rse, UserRole.EDITEUR)
    invitation = Invitation.objects.create(
        entreprise=entreprise,
        email="alice@test.com",
        role=UserRole.PROPRIETAIRE,
        inviteur=conseiller_rse,
        est_invitation_proprietaire_tiers=True,
    )
    # Simuler l'acceptation
    invitation.accepter(alice)

    assert not entreprise.est_structure_vacante
