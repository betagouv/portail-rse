from datetime import datetime
from datetime import timedelta
from datetime import timezone

import pytest
from django.db import IntegrityError
from freezegun import freeze_time

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
    assert entreprise.bdese_accord is False
    assert entreprise.effectif is None
    assert not entreprise.users.all()
    assert not entreprise.is_qualified

    with pytest.raises(IntegrityError):
        Entreprise.objects.create(
            siren="123456789", denomination="Autre Entreprise SAS"
        )

    with freeze_time(now + timedelta(1)):
        entreprise.effectif = Entreprise.EFFECTIF_ENTRE_50_ET_299
        entreprise.save()

    assert entreprise.updated_at == now + timedelta(1)


@pytest.mark.django_db(transaction=True)
def test_entreprise_is_qualified(unqualified_entreprise):
    assert not unqualified_entreprise.is_qualified

    unqualified_entreprise.effectif = Entreprise.EFFECTIF_ENTRE_50_ET_299

    assert unqualified_entreprise.is_qualified
