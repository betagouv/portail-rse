from datetime import datetime
from datetime import timezone

from freezegun import freeze_time

from habilitations.models import attach_user_to_entreprise
from habilitations.models import get_habilitation
from habilitations.models import is_user_attached_to_entreprise


def test_habilitation(alice, entreprise_factory):
    entreprise = entreprise_factory()
    assert not is_user_attached_to_entreprise(alice, entreprise)

    created_at = datetime(2023, 1, 27, 16, 1, tzinfo=timezone.utc)
    with freeze_time(created_at):
        attach_user_to_entreprise(alice, entreprise, "présidente")

    assert entreprise in alice.entreprises.all()
    habilitation = get_habilitation(alice, entreprise)
    assert habilitation.fonctions == "présidente"
    assert habilitation.created_at == created_at

    confirmed_at = datetime(2023, 2, 14, 8, 15, tzinfo=timezone.utc)
    with freeze_time(confirmed_at):
        habilitation.confirm()

    assert habilitation.is_confirmed
    assert habilitation.confirmed_at == confirmed_at
