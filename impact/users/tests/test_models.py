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


@pytest.mark.django_db
@pytest.mark.parametrize("est_francais", [True, False])
def test_est_etranger_est_l_inverse_de_est_francais(django_user_model, est_francais):
    utilisateur = django_user_model.objects.create(
        email="nouveau@test.fr", est_francais=est_francais
    )

    assert utilisateur.est_etranger is not est_francais


@pytest.mark.django_db
@pytest.mark.parametrize(
    "est_francais,code_pays,peut_etre_membre",
    [
        (True, "FRA", True),
        (True, "MAR", True),
        (False, "MAR", True),
        (False, "FRA", False),
    ],
)
def test_peut_etre_membre_d_une_entreprise(
    django_user_model, entreprise_factory, est_francais, code_pays, peut_etre_membre
):
    utilisateur = django_user_model.objects.create(
        email="nouveau@test.fr", est_francais=est_francais
    )
    entreprise = entreprise_factory(code_pays=code_pays, identifiant="001561191000066")

    assert utilisateur.peut_etre_membre(entreprise) is peut_etre_membre
