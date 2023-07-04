from datetime import datetime
from datetime import timedelta
from datetime import timezone

import pytest
from django.db import IntegrityError
from freezegun import freeze_time

from entreprises.models import CaracteristiquesAnnuelles
from entreprises.models import Entreprise


@pytest.mark.django_db(transaction=True)
def test_entreprise():
    now = datetime(2023, 1, 27, 16, 1, tzinfo=timezone.utc)

    with freeze_time(now):
        entreprise = Entreprise.objects.create(
            siren="123456789", denomination="Entreprise SAS"
        )

    assert entreprise.created_at == now
    assert entreprise.updated_at == now
    assert entreprise.siren == "123456789"
    assert entreprise.denomination == "Entreprise SAS"
    assert not entreprise.users.all()
    assert not entreprise.est_qualifiee

    with pytest.raises(IntegrityError):
        Entreprise.objects.create(
            siren="123456789", denomination="Autre Entreprise SAS"
        )

    with freeze_time(now + timedelta(1)):
        entreprise.denomination = "Nouveau nom SAS"
        entreprise.save()

    assert entreprise.updated_at == now + timedelta(1)


@pytest.mark.django_db(transaction=True)
def test_entreprise_est_qualifiee(entreprise_non_qualifiee):
    assert not entreprise_non_qualifiee.est_qualifiee

    caracteristiques = entreprise_non_qualifiee.actualise_caracteristiques(
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50,
        effectif_outre_mer=CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_MOINS_DE_250,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_700K,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_350K,
        bdese_accord=True,
        systeme_management_energie=True,
    )
    caracteristiques.save()

    assert entreprise_non_qualifiee.est_qualifiee


def test_actualise_caracteristiques(entreprise_non_qualifiee):
    assert entreprise_non_qualifiee.caracteristiques_actuelles() is None

    effectif = CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499
    tranche_chiffre_affaires = CaracteristiquesAnnuelles.CA_MOINS_DE_700K
    tranche_bilan = CaracteristiquesAnnuelles.BILAN_MOINS_DE_350K
    bdese_accord = False
    systeme_management_energie = False

    caracteristiques = entreprise_non_qualifiee.actualise_caracteristiques(
        effectif,
        tranche_chiffre_affaires,
        tranche_bilan,
        bdese_accord,
        systeme_management_energie,
    )
    caracteristiques.save()

    assert caracteristiques.effectif == effectif
    assert caracteristiques.tranche_chiffre_affaires == tranche_chiffre_affaires
    assert caracteristiques.tranche_bilan == tranche_bilan
    assert caracteristiques.bdese_accord == bdese_accord
    assert caracteristiques.systeme_management_energie == systeme_management_energie
    entreprise_non_qualifiee.refresh_from_db()
    assert entreprise_non_qualifiee.caracteristiques_actuelles() == caracteristiques

    nouvel_effectif = CaracteristiquesAnnuelles.EFFECTIF_500_ET_PLUS
    nouvelle_tranche_chiffre_affaires = CaracteristiquesAnnuelles.CA_ENTRE_700K_ET_12M
    nouvelle_tranche_bilan = CaracteristiquesAnnuelles.BILAN_ENTRE_6M_ET_20M
    nouveau_bdese_accord = True
    nouveau_systeme_management_energie = True

    nouvelles_caracteristiques = entreprise_non_qualifiee.actualise_caracteristiques(
        nouvel_effectif,
        nouvelle_tranche_chiffre_affaires,
        nouvelle_tranche_bilan,
        nouveau_bdese_accord,
        nouveau_systeme_management_energie,
    )
    nouvelles_caracteristiques.save()

    assert nouvelles_caracteristiques.effectif == nouvel_effectif
    assert (
        nouvelles_caracteristiques.tranche_chiffre_affaires
        == nouvelle_tranche_chiffre_affaires
    )
    assert nouvelles_caracteristiques.tranche_bilan == nouvelle_tranche_bilan
    assert nouvelles_caracteristiques.bdese_accord == nouveau_bdese_accord
    assert (
        nouvelles_caracteristiques.systeme_management_energie
        == nouveau_systeme_management_energie
    )
    entreprise_non_qualifiee.refresh_from_db()
    assert (
        entreprise_non_qualifiee.caracteristiques_actuelles()
        == nouvelles_caracteristiques
    )


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
