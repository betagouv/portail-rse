import pytest


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
def test_utilisateur_francais_par_defaut(django_user_model):
    utilisateur = django_user_model.objects.create(email="nouveau@test.fr")

    assert utilisateur.est_francais


@pytest.mark.django_db
def test_utilisateur_etranger_n_a_pas_a_choisir_son_type(django_user_model):
    utilisateur = django_user_model.objects.create(
        email="nouveau@test.fr", est_francais=False
    )

    assert not utilisateur.doit_choisir_type_utilisateur
