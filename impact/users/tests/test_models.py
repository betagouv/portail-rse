import pytest
from django.utils import timezone

from users.models import anonymise_un_utilisateur

# Tests pour la propriété doit_choisir_type_utilisateur


@pytest.mark.django_db
def test_nouvel_utilisateur_doit_choisir_type(django_user_model):
    """Un nouvel utilisateur sans habilitation doit choisir son type."""
    utilisateur = django_user_model.objects.create(
        email="nouveau@test.fr",
    )

    assert utilisateur.doit_choisir_type_utilisateur


@pytest.mark.django_db
def test_conseiller_rse_na_pas_a_choisir(conseiller_rse):
    """Un conseiller RSE n'a pas à choisir son type."""
    assert not conseiller_rse.doit_choisir_type_utilisateur


@pytest.mark.django_db
def test_connexion_annule_alerte_anonymisation(client, alice):
    alice.date_alerte_anonymisation = timezone.now()
    alice.save()

    client.force_login(alice)

    alice.refresh_from_db()
    assert alice.date_alerte_anonymisation is None


@pytest.mark.django_db
def test_anonymise_un_utilisateur(alice):
    assert not alice.est_anonyme

    anonymise_un_utilisateur(alice)

    alice.refresh_from_db()
    assert alice.est_anonyme
    assert alice.prenom == "Personne"
    assert alice.nom == "anonymisée"
    assert alice.email == str(alice.id) + "@anonyme.invalid"
    assert not alice.is_active
    assert alice.oidc_sub_id is None
    assert not alice.has_usable_password()
