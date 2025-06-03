from datetime import datetime
from datetime import timedelta
from datetime import timezone

from django.conf import settings
from freezegun import freeze_time

from invitations.models import Invitation


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


def test_inviteur_supprimé_après_la_creation_de_l_invitation(
    db, alice, entreprise_non_qualifiee
):
    invitation = Invitation.objects.create(
        entreprise=entreprise_non_qualifiee, email="bob@domaine.test", inviteur=alice
    )

    alice.delete()

    invitation.refresh_from_db()
    assert invitation.inviteur is None
