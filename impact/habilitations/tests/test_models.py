import pytest

from habilitations.models import Habilitation
from habilitations.models import UserRole
from invitations.models import Invitation


@pytest.mark.django_db
def test_ajouter_habilitation(alice, entreprise_factory):
    entreprise = entreprise_factory()
    Habilitation.ajouter(entreprise, alice, UserRole.PROPRIETAIRE, "présidente")

    habilitation = Habilitation.objects.pour(entreprise, alice)

    assert habilitation, "Il devrait exister une habilitation"
    assert habilitation.fonctions == "présidente", "La fonction est incorrecte"
    assert habilitation.role == UserRole.PROPRIETAIRE, "Le rôle est incorrect"


@pytest.mark.django_db
def test_retirer_habilitation(alice, entreprise_factory):
    entreprise = entreprise_factory()
    Habilitation.ajouter(entreprise, alice, UserRole.PROPRIETAIRE, "présidente")
    Habilitation.retirer(entreprise, alice)

    with pytest.raises(Habilitation.DoesNotExist):
        Habilitation.objects.pour(entreprise, alice)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role", [UserRole.PROPRIETAIRE, UserRole.LECTEUR, UserRole.EDITEUR]
)
def test_ajouter_habilitation_avec_differents_roles(alice, entreprise_factory, role):
    entreprise = entreprise_factory()
    Habilitation.ajouter(entreprise, alice, role, "présidente")

    habilitation = Habilitation.objects.pour(entreprise, alice)

    assert habilitation, "Il devrait exister une habilitation"
    assert habilitation.fonctions == "présidente", "La fonction est incorrecte"
    assert habilitation.role == role, "Le rôle est incorrect"


def test_ajouter_habilitation_avec_invitation(alice, entreprise_factory):
    entreprise = entreprise_factory()
    invitation = Invitation.objects.create(entreprise=entreprise)

    Habilitation.ajouter(entreprise, alice, invitation=invitation)

    habilitation = Habilitation.objects.pour(entreprise, alice)
    assert habilitation.invitation == invitation
