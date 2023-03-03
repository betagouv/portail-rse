from datetime import datetime, timezone, timedelta

from django.db import IntegrityError
from freezegun import freeze_time
import pytest

from entreprises.models import add_user_in_entreprise, get_habilitation, Entreprise


@pytest.mark.django_db(transaction=True)
def test_entreprise():
    now = datetime(2023, 1, 27, 16, 1, tzinfo=timezone.utc)

    with freeze_time(now):
        entreprise = Entreprise.objects.create(siren="123456789")

    assert entreprise.created_at == now
    assert entreprise.updated_at == now
    assert entreprise.siren == "123456789"
    assert entreprise.raison_sociale == ""
    assert entreprise.bdese_accord is False
    assert entreprise.effectif == ""
    assert not entreprise.users.all()

    with pytest.raises(IntegrityError):
        Entreprise.objects.create(siren="123456789")

    with freeze_time(now + timedelta(1)):
        entreprise.raison_sociale = "Entreprise SAS"
        entreprise.save()

    assert entreprise.updated_at == now + timedelta(1)


def test_relation_user_entreprise(alice, entreprise_factory):
    entreprise = entreprise_factory()
    assert get_habilitation(alice, entreprise) == None

    add_user_in_entreprise(alice, entreprise, "présidente")

    assert entreprise in alice.entreprises.all()
    assert get_habilitation(alice, entreprise).fonctions == "présidente"
