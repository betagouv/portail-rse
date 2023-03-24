from datetime import datetime
from datetime import timezone

from freezegun import freeze_time

from habilitations.models import add_entreprise_to_user
from habilitations.models import get_habilitation


def test_habilitation(alice, entreprise_factory):
    entreprise = entreprise_factory()
    assert get_habilitation(entreprise, alice) == None

    add_entreprise_to_user(entreprise, alice, "présidente")

    assert entreprise in alice.entreprises.all()
    habilitation = get_habilitation(entreprise, alice)
    assert habilitation.fonctions == "présidente"

    now = datetime(2023, 1, 27, 16, 1, tzinfo=timezone.utc)
    with freeze_time(now):
        habilitation.confirm()

    assert habilitation.is_confirmed
    assert habilitation.confirmed_at == now
