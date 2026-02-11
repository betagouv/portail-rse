import pytest

from habilitations.enums import UserRole
from habilitations.models import Habilitation


# Tests pour la propriété doit_choisir_type_utilisateur


@pytest.mark.django_db
def test_nouvel_utilisateur_doit_choisir_type(django_user_model):
    """Un nouvel utilisateur sans habilitation doit choisir son type."""
    utilisateur = django_user_model.objects.create(
        email="nouveau@test.fr",
        is_conseiller_rse=False,
    )

    assert utilisateur.doit_choisir_type_utilisateur


@pytest.mark.django_db
def test_conseiller_rse_na_pas_a_choisir(conseiller_rse):
    """Un conseiller RSE n'a pas à choisir son type."""
    assert not conseiller_rse.doit_choisir_type_utilisateur


@pytest.mark.django_db
def test_membre_entreprise_na_pas_a_choisir(alice, entreprise_factory):
    """Un membre d'entreprise (avec habilitation) n'a pas à choisir son type."""
    entreprise = entreprise_factory()
    Habilitation.ajouter(entreprise, alice, UserRole.PROPRIETAIRE)

    assert not alice.doit_choisir_type_utilisateur


@pytest.mark.django_db
def test_conseiller_rse_avec_habilitation_na_pas_a_choisir(
    conseiller_rse, entreprise_factory
):
    """Un conseiller RSE avec habilitation n'a pas à choisir son type."""
    entreprise = entreprise_factory()
    Habilitation.ajouter(entreprise, conseiller_rse, UserRole.EDITEUR)

    assert not conseiller_rse.doit_choisir_type_utilisateur
