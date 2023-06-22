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
def test_synchronise_une_entreprise(entreprise_factory):
    with freeze_time("2023-06-12 12:00"):
        entreprise_A = entreprise_factory(
            siren="000000001",
            denomination="A",
            effectif=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499,
            bdese_accord=True,
        )
    date_deuxieme_evolution = datetime(2024, 7, 13, tzinfo=timezone.utc)
    date_troisieme_evolution = datetime(2025, 8, 14, tzinfo=timezone.utc)
    with freeze_time(date_deuxieme_evolution) as frozen_datetime:
        CaracteristiquesAnnuelles.objects.create(
            entreprise=entreprise_A,
            annee=2024,
            effectif=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499,
            bdese_accord=True,
        )
        frozen_datetime.move_to(date_troisieme_evolution)
        CaracteristiquesAnnuelles.objects.create(
            entreprise=entreprise_A,
            annee=2025,
            effectif=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499,
            bdese_accord=True,
        )

    Command().handle()

    assert MetabaseEntreprise.objects.count() == 1
    metabase_entreprise = MetabaseEntreprise.objects.first()
    assert metabase_entreprise.denomination == "A"
    assert metabase_entreprise.siren == "000000001"
    assert metabase_entreprise.effectif == "300-499"
    assert metabase_entreprise.bdese_accord == True
    assert metabase_entreprise.ajoutee_le == entreprise_A.created_at
    assert metabase_entreprise.modifiee_le == date_troisieme_evolution
    assert metabase_entreprise.nombre_utilisateurs == 0


@pytest.mark.django_db(transaction=True, databases=["default", METABASE_DATABASE_NAME])
def test_synchronise_une_entreprise_plusieurs_fois(entreprise_factory):
    entreprise_A = entreprise_factory(
        siren="000000001",
        denomination="A",
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50,
        bdese_accord=True,
    )

    Command().handle()
    Command().handle()

    assert MetabaseEntreprise.objects.count() == 1
    metabase_entreprise = MetabaseEntreprise.objects.first()
    assert metabase_entreprise.denomination == "A"
    assert metabase_entreprise.siren == "000000001"
    assert metabase_entreprise.effectif == "0-49"
    assert metabase_entreprise.bdese_accord == True
    assert metabase_entreprise.nombre_utilisateurs == 0


@pytest.mark.django_db(transaction=True, databases=["default", METABASE_DATABASE_NAME])
def test_synchronise_une_entreprise_sans_caracteristiques_actuelles():
    entreprise = Entreprise.objects.create(
        siren="000000001", denomination="Entreprise SAS"
    )

    Command().handle()

    metabase_entreprise = MetabaseEntreprise.objects.first()
    assert metabase_entreprise.denomination == "Entreprise SAS"
    assert metabase_entreprise.siren == "000000001"
    assert metabase_entreprise.effectif is None
    assert metabase_entreprise.bdese_accord is None


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
    attach_user_to_entreprise(utilisateur, entreprise, "Présidente")

    Command().handle()

    metabase_entreprise = MetabaseEntreprise.objects.first()
    assert metabase_entreprise.nombre_utilisateurs == 1

    assert MetabaseUtilisateur.objects.count() == 1
    metabase_utilisateur = MetabaseUtilisateur.objects.first()
    assert metabase_utilisateur.impact_id == utilisateur.pk
    assert metabase_utilisateur.reception_actualites is False
    assert metabase_utilisateur.email_confirme is True

    assert MetabaseHabilitation.objects.count() == 1
    metabase_habilitation = MetabaseHabilitation.objects.first()
    assert metabase_habilitation.utilisateur == metabase_utilisateur
    assert metabase_habilitation.entreprise == metabase_entreprise
    assert metabase_habilitation.fonctions == "Présidente"
    assert not metabase_habilitation.confirmee_le
