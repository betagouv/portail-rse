from datetime import datetime
from datetime import timedelta
from datetime import timezone

import pytest
from django.db import IntegrityError
from freezegun import freeze_time

from entreprises.models import Entreprise
from entreprises.models import Evolution


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
    assert not entreprise.is_qualified

    with pytest.raises(IntegrityError):
        Entreprise.objects.create(
            siren="123456789", denomination="Autre Entreprise SAS"
        )

    with freeze_time(now + timedelta(1)):
        entreprise.denomination = "Nouveau nom SAS"
        entreprise.save()

    assert entreprise.updated_at == now + timedelta(1)


@pytest.mark.django_db(transaction=True)
def test_entreprise_is_qualified(unqualified_entreprise):
    assert not unqualified_entreprise.is_qualified

    evolution = unqualified_entreprise.set_current_evolution(
        effectif=Evolution.EFFECTIF_MOINS_DE_50,
        bdese_accord=True,
    )
    evolution.save()

    assert unqualified_entreprise.is_qualified


def test_get_and_set_current_evolution(unqualified_entreprise):
    assert unqualified_entreprise.get_current_evolution() is None

    effectif = Evolution.EFFECTIF_ENTRE_300_ET_499
    bdese_accord = False

    evolution = unqualified_entreprise.set_current_evolution(effectif, bdese_accord)
    evolution.save()

    assert evolution.effectif == effectif
    assert evolution.bdese_accord == bdese_accord
    unqualified_entreprise.refresh_from_db()
    assert unqualified_entreprise.get_current_evolution() == evolution

    effectif_corrige = Evolution.EFFECTIF_500_ET_PLUS
    bdese_accord_corrige = True

    evolution_corrigee = unqualified_entreprise.set_current_evolution(
        effectif_corrige, bdese_accord_corrige
    )
    evolution_corrigee.save()

    assert evolution_corrigee.effectif == effectif_corrige
    assert evolution_corrigee.bdese_accord == bdese_accord_corrige
    unqualified_entreprise.refresh_from_db()
    assert unqualified_entreprise.get_current_evolution() == evolution_corrigee


def test_uniques_caracteristiques_annuelles(unqualified_entreprise):
    evolution = Evolution(entreprise=unqualified_entreprise, annee=2023)
    evolution.save()

    with pytest.raises(IntegrityError):
        evolution_bis = Evolution(entreprise=unqualified_entreprise, annee=2023)
        evolution_bis.save()
