from datetime import datetime
from datetime import timedelta
from datetime import timezone

from django.conf import settings
from freezegun import freeze_time

from habilitations.models import Habilitation
from habilitations.models import UserRole
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


def test_accepter(alice, entreprise_factory, django_user_model):
    entreprise = entreprise_factory()
    invitation = Invitation.objects.create(
        entreprise=entreprise,
        email="bob@domaine.test",
        inviteur=alice,
        role=UserRole.EDITEUR,
    )
    date_acceptation = datetime(2025, 5, 9, 14, 30, tzinfo=timezone.utc)
    bob = django_user_model.objects.create(
        prenom="Bob",
        nom="Dylan",
        email="bob@domaine.test",
    )

    with freeze_time(date_acceptation):
        invitation.accepter(bob, fonctions="Testeur")

    invitation.refresh_from_db()
    assert invitation.date_acceptation == date_acceptation

    habilitation = Habilitation.pour(entreprise, bob)
    assert habilitation.fonctions == "Testeur"
    assert habilitation.invitation == invitation
    assert habilitation.role == UserRole.EDITEUR
