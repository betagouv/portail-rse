import pytest

from habilitations.enums import UserRole
from habilitations.models import Habilitation
from habilitations.models import HabilitationError
from invitations.models import Invitation


@pytest.fixture
def conseiller_rse(django_user_model):
    return django_user_model.objects.create(
        prenom="Claire",
        nom="Conseillère",
        email="claire@conseil-rse.test",
        is_email_confirmed=True,
        is_conseiller_rse=True,
    )


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
    h = Habilitation.pour(entreprise, alice)

    with pytest.raises(HabilitationError):
        Habilitation.retirer(entreprise, alice)

    h.role = UserRole.EDITEUR
    h.save()
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


# Tests pour les conseillers RSE


@pytest.mark.django_db
def test_conseiller_rse_ne_peut_pas_etre_proprietaire(
    conseiller_rse, entreprise_factory
):
    """Un conseiller RSE ne peut pas obtenir le rôle PROPRIETAIRE."""
    entreprise = entreprise_factory()

    with pytest.raises(HabilitationError) as exc_info:
        Habilitation.ajouter(entreprise, conseiller_rse, UserRole.PROPRIETAIRE)

    assert "conseiller RSE ne peut pas être propriétaire" in str(exc_info.value)


@pytest.mark.django_db
def test_conseiller_rse_peut_etre_editeur(conseiller_rse, entreprise_factory):
    """Un conseiller RSE peut obtenir le rôle EDITEUR."""
    entreprise = entreprise_factory()

    Habilitation.ajouter(entreprise, conseiller_rse, UserRole.EDITEUR, "Consultant RSE")

    habilitation = Habilitation.objects.pour(entreprise, conseiller_rse)
    assert habilitation.role == UserRole.EDITEUR
    assert habilitation.fonctions == "Consultant RSE"


@pytest.mark.django_db
def test_utilisateur_standard_peut_etre_proprietaire(alice, entreprise_factory):
    """Un utilisateur standard (non conseiller) peut être propriétaire."""
    entreprise = entreprise_factory()

    assert not alice.is_conseiller_rse

    Habilitation.ajouter(entreprise, alice, UserRole.PROPRIETAIRE, "Présidente")

    habilitation = Habilitation.objects.pour(entreprise, alice)
    assert habilitation.role == UserRole.PROPRIETAIRE
