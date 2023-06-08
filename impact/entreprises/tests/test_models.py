from datetime import datetime
from datetime import timedelta
from datetime import timezone

import pytest
from django.db import IntegrityError
from freezegun import freeze_time

from entreprises.models import Entreprise
from entreprises.models import Evolution
from entreprises.models import set_current_evolution


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

    set_current_evolution(
        entreprise=unqualified_entreprise,
        effectif=Evolution.EFFECTIF_MOINS_DE_50,
        bdese_accord=True,
    )

    assert unqualified_entreprise.is_qualified
