from datetime import datetime
from datetime import timezone

import pytest
from freezegun import freeze_time

from entreprises.models import CaracteristiquesAnnuelles
from entreprises.models import Entreprise
from habilitations.models import attach_user_to_entreprise
from impact.settings import METABASE_DATABASE_NAME
from metabase.management.commands.sync_metabase import Command
from metabase.models import Entreprise as MetabaseEntreprise
from metabase.models import Habilitation as MetabaseHabilitation
from metabase.models import Utilisateur as MetabaseUtilisateur


@pytest.mark.django_db(transaction=True, databases=["default", METABASE_DATABASE_NAME])
def test_synchronise_une_entreprise_qualifiee(
    entreprise_factory, date_cloture_dernier_exercice
):
    date_creation = datetime(
        date_cloture_dernier_exercice.year,
        date_cloture_dernier_exercice.month,
        date_cloture_dernier_exercice.day,
        tzinfo=timezone.utc,
    )
    date_deuxieme_evolution = datetime(
        date_cloture_dernier_exercice.year + 1,
        date_cloture_dernier_exercice.month,
        date_cloture_dernier_exercice.day,
        tzinfo=timezone.utc,
    )
    date_troisieme_evolution = datetime(
        date_cloture_dernier_exercice.year + 2,
        date_cloture_dernier_exercice.month,
        date_cloture_dernier_exercice.day,
        tzinfo=timezone.utc,
    )
    with freeze_time(date_creation) as frozen_datetime:
        entreprise = entreprise_factory(
            siren="000000001",
            denomination="Entreprise A",
            date_cloture_exercice=date_cloture_dernier_exercice,
            effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50,
            effectif_outre_mer=CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_MOINS_DE_250,
            tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_700K,
            tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_350K,
            bdese_accord=False,
            systeme_management_energie=False,
        )
        frozen_datetime.move_to(date_deuxieme_evolution)
        entreprise.actualise_caracteristiques(
            date_cloture_exercice=date_cloture_dernier_exercice.replace(
                year=date_cloture_dernier_exercice.year + 1
            ),
            effectif=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
            effectif_outre_mer=CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_MOINS_DE_250,
            tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_ENTRE_700K_ET_12M,
            tranche_bilan=CaracteristiquesAnnuelles.BILAN_ENTRE_350K_ET_6M,
            tranche_chiffre_affaires_consolide=None,
            tranche_bilan_consolide=None,
            bdese_accord=True,
            systeme_management_energie=False,
        ).save()
        frozen_datetime.move_to(date_troisieme_evolution)
        entreprise.actualise_caracteristiques(
            date_cloture_exercice=date_cloture_dernier_exercice.replace(
                year=date_cloture_dernier_exercice.year + 2
            ),
            effectif=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499,
            effectif_outre_mer=CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_MOINS_DE_250,
            tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_ENTRE_12M_ET_40M,
            tranche_bilan=CaracteristiquesAnnuelles.BILAN_ENTRE_6M_ET_20M,
            tranche_chiffre_affaires_consolide=None,
            tranche_bilan_consolide=None,
            bdese_accord=True,
            systeme_management_energie=True,
        ).save()

    Command().handle()

    assert MetabaseEntreprise.objects.count() == 1
    metabase_entreprise = MetabaseEntreprise.objects.first()
    assert metabase_entreprise.pk == metabase_entreprise.impact_id == entreprise.pk
    assert metabase_entreprise.ajoutee_le == date_creation
    assert metabase_entreprise.modifiee_le == date_troisieme_evolution
    assert metabase_entreprise.siren == "000000001"
    assert metabase_entreprise.denomination == "Entreprise A"
    assert (
        metabase_entreprise.date_cloture_exercice
        == date_cloture_dernier_exercice.replace(
            year=date_cloture_dernier_exercice.year + 2
        )
    )
    assert metabase_entreprise.effectif == "300-499"
    assert metabase_entreprise.tranche_bilan == "6M-20M"
    assert metabase_entreprise.tranche_chiffre_affaires == "12M-40M"
    assert metabase_entreprise.bdese_accord is True
    assert metabase_entreprise.systeme_management_energie is True
    assert metabase_entreprise.nombre_utilisateurs == 0


@pytest.mark.django_db(transaction=True, databases=["default", METABASE_DATABASE_NAME])
def test_synchronise_une_entreprise_plusieurs_fois(entreprise_factory):
    entreprise = entreprise_factory(
        siren="000000001",
        denomination="Entreprise A",
    )

    Command().handle()
    Command().handle()

    assert MetabaseEntreprise.objects.count() == 1
    metabase_entreprise = MetabaseEntreprise.objects.first()
    assert metabase_entreprise.impact_id == entreprise.pk
    assert metabase_entreprise.siren == "000000001"
    assert metabase_entreprise.denomination == "Entreprise A"


@pytest.mark.django_db(transaction=True, databases=["default", METABASE_DATABASE_NAME])
def test_synchronise_une_entreprise_sans_caracteristiques_annuelles():
    entreprise = Entreprise.objects.create(
        siren="000000001", denomination="Entreprise SAS"
    )

    Command().handle()

    metabase_entreprise = MetabaseEntreprise.objects.first()
    assert metabase_entreprise.denomination == "Entreprise SAS"
    assert metabase_entreprise.siren == "000000001"
    assert metabase_entreprise.date_cloture_exercice is None
    assert metabase_entreprise.effectif is None
    assert metabase_entreprise.tranche_chiffre_affaires is None
    assert metabase_entreprise.tranche_bilan is None
    assert metabase_entreprise.bdese_accord is None
    assert metabase_entreprise.systeme_management_energie is None


@pytest.mark.django_db(transaction=True, databases=["default", METABASE_DATABASE_NAME])
def test_synchronise_une_entreprise_sans_caracteristiques_qualifiantes(
    entreprise_factory,
):
    # Ce cas arrive lorsqu'on ajoute une nouvelle caracteristique qualifiante dans les caracteristiques annuelles
    # Les anciennes caracteristiques ne sont plus qualifiantes mais on veut quand même les avoir dans metabase
    entreprise = entreprise_factory()
    caracteristiques = entreprise.dernieres_caracteristiques_qualifiantes
    tranche_bilan = caracteristiques.tranche_bilan
    caracteristiques.tranche_chiffre_affaires = None
    caracteristiques.save()

    Command().handle()

    metabase_entreprise = MetabaseEntreprise.objects.first()
    assert metabase_entreprise.tranche_bilan == tranche_bilan
    assert metabase_entreprise.tranche_chiffre_affaires is None


@pytest.mark.django_db(transaction=True, databases=["default", METABASE_DATABASE_NAME])
def test_synchronise_une_entreprise_avec_un_utilisateur(
    entreprise_factory, django_user_model
):
    entreprise = entreprise_factory()
    utilisateur = django_user_model.objects.create(
        prenom="Alice",
        nom="Cooper",
        email="alice@impact.test",
        reception_actualites=False,
        is_email_confirmed=True,
    )
    habilitation = attach_user_to_entreprise(utilisateur, entreprise, "Présidente")

    Command().handle()

    metabase_entreprise = MetabaseEntreprise.objects.first()
    assert metabase_entreprise.nombre_utilisateurs == 1

    assert MetabaseUtilisateur.objects.count() == 1
    metabase_utilisateur = MetabaseUtilisateur.objects.first()
    assert metabase_utilisateur.pk == metabase_utilisateur.impact_id == utilisateur.pk
    assert metabase_utilisateur.ajoute_le == utilisateur.created_at
    assert metabase_utilisateur.modifie_le == utilisateur.updated_at
    assert metabase_utilisateur.reception_actualites is False
    assert metabase_utilisateur.email_confirme is True

    assert MetabaseHabilitation.objects.count() == 1
    metabase_habilitation = MetabaseHabilitation.objects.first()
    assert (
        metabase_habilitation.pk == metabase_habilitation.impact_id == habilitation.pk
    )
    assert metabase_habilitation.ajoutee_le == habilitation.created_at
    assert metabase_habilitation.modifiee_le == habilitation.updated_at
    assert metabase_habilitation.utilisateur == metabase_utilisateur
    assert metabase_habilitation.entreprise == metabase_entreprise
    assert metabase_habilitation.fonctions == "Présidente"
    assert not metabase_habilitation.confirmee_le
