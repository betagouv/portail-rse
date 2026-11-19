import pytest

from habilitations.enums import UserRole
from habilitations.models import Habilitation
from habilitations.models import HabilitationError
from invitations.models import Invitation


@pytest.mark.django_db
def test_ajouter_habilitation(alice, entreprise_factory):
    entreprise = entreprise_factory()
    Habilitation.ajouter(entreprise, alice, UserRole.ADMINISTRATEUR, "présidente")

    habilitation = Habilitation.objects.pour(entreprise, alice)

    assert habilitation, "Il devrait exister une habilitation"
    assert habilitation.fonctions == "présidente", "La fonction est incorrecte"
    assert habilitation.role == UserRole.ADMINISTRATEUR, "Le rôle est incorrect"


@pytest.mark.django_db
def test_retirer_habilitation(alice, entreprise_factory):
    entreprise = entreprise_factory()
    Habilitation.ajouter(entreprise, alice, UserRole.ADMINISTRATEUR, "présidente")
    h = Habilitation.pour(entreprise, alice)

    with pytest.raises(HabilitationError):
        Habilitation.retirer(entreprise, alice)

    h.role = UserRole.CONTRIBUTEUR
    h.save()
    Habilitation.retirer(entreprise, alice)

    with pytest.raises(Habilitation.DoesNotExist):
        Habilitation.objects.pour(entreprise, alice)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role", [UserRole.ADMINISTRATEUR, UserRole.LECTEUR, UserRole.CONTRIBUTEUR]
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
@pytest.mark.parametrize("is_conseiller_rse", [True, False])
@pytest.mark.parametrize("role", [UserRole.ADMINISTRATEUR, UserRole.CONTRIBUTEUR])
def test_etat_conseiller_rse_est_independant_des_droits(
    is_conseiller_rse, role, alice, entreprise_factory
):
    """Un conseiller RSE peut obtenir le rôle ADMINISTRATEUR."""
    entreprise = entreprise_factory()
    alice.is_conseiller_rse = is_conseiller_rse
    alice.save()

    Habilitation.ajouter(entreprise, alice, role=role)

    habilitation = Habilitation.objects.pour(entreprise, alice)
    assert habilitation.role == role


@pytest.mark.django_db
def test_un_compte_etranger_ne_peut_pas_etre_ajoute_a_une_entreprise_francaise(
    alice, entreprise_factory
):
    alice.est_francais = False
    alice.save()
    entreprise = entreprise_factory()

    with pytest.raises(HabilitationError) as erreur:
        Habilitation.ajouter(entreprise, alice)

    assert (
        str(erreur.value)
        == "Ce compte est limité aux entreprises sans SIREN : connectez-vous avec ProConnect pour rejoindre une entreprise avec SIREN."
    )
    assert not Habilitation.existe(entreprise, alice)


@pytest.mark.django_db
def test_un_compte_etranger_peut_etre_ajoute_a_une_entreprise_etrangere(
    alice, entreprise_factory
):
    alice.est_francais = False
    alice.save()
    entreprise = entreprise_factory(code_pays="MAR", identifiant="001561191000066")

    Habilitation.ajouter(entreprise, alice)

    assert Habilitation.existe(entreprise, alice)
