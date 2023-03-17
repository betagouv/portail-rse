from datetime import datetime, timezone, timedelta

from django.db import IntegrityError
from freezegun import freeze_time
import pytest

from entreprises.models import Entreprise


@pytest.mark.django_db(transaction=True)
def test_entreprise():
    now = datetime(2023, 1, 27, 16, 1, tzinfo=timezone.utc)

    with freeze_time(now):
        entreprise = Entreprise.objects.create(
            siren="123456789", raison_sociale="Entreprise SAS"
        )

    assert entreprise.created_at == now
    assert entreprise.updated_at == now
    assert entreprise.siren == "123456789"
    assert entreprise.raison_sociale == "Entreprise SAS"
    assert entreprise.bdese_accord is False
    assert entreprise.effectif is None
    assert not entreprise.users.all()
    assert not entreprise.is_qualified

    with pytest.raises(IntegrityError):
        Entreprise.objects.create(
            siren="123456789", raison_sociale="Autre Entreprise SAS"
        )

    with freeze_time(now + timedelta(1)):
        entreprise.effectif = "moyen"
        entreprise.save()

    assert entreprise.updated_at == now + timedelta(1)


@pytest.mark.django_db(transaction=True)
def test_entreprise_is_qualified(unqualified_entreprise):
    assert not unqualified_entreprise.is_qualified

    unqualified_entreprise.effectif = "moyen"

    assert unqualified_entreprise.is_qualified
