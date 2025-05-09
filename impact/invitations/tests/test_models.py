from datetime import datetime
from datetime import timedelta
from datetime import timezone

from django.conf import settings
from freezegun import freeze_time

from invitations.models import CODE_MAX_LENGTH
from invitations.models import cree_code_invitation
from invitations.models import Invitation


def test_cree_code_invitation():
    assert len(cree_code_invitation()) == CODE_MAX_LENGTH
    assert cree_code_invitation() != cree_code_invitation()


def test_date_d_expiration_d_une_invitation(db, entreprise_non_qualifiee):
    now = datetime(2025, 5, 9, 14, 30, tzinfo=timezone.utc)
    with freeze_time(now):
        invitation = Invitation.objects.create(
            entreprise=entreprise_non_qualifiee, email="alice@domaine.test"
        )

    assert invitation.date_expiration == now + timedelta(
        seconds=settings.INVITATION_MAX_AGE
    )


def test_invitation_expirée(db, entreprise_non_qualifiee):
    now = datetime(2025, 5, 9, 14, 30, tzinfo=timezone.utc)
    with freeze_time(now):
        invitation = Invitation.objects.create(
            entreprise=entreprise_non_qualifiee, email="alice@domaine.test"
        )

    with freeze_time(now + timedelta(seconds=settings.INVITATION_MAX_AGE - 1)):
        assert not invitation.est_expiree

    with freeze_time(now + timedelta(seconds=settings.INVITATION_MAX_AGE + 1)):
        assert invitation.est_expiree
