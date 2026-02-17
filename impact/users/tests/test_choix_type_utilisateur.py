import pytest
from django.urls import reverse

from users.forms import ChoixTypeUtilisateurForm


@pytest.mark.django_db
def test_choix_type_utilisateur_affiche_formulaire(client, django_user_model):
    """La vue affiche le formulaire de choix pour un nouvel utilisateur."""
    utilisateur = django_user_model.objects.create(
        email="nouveau@test.fr",
    )
    client.force_login(utilisateur)

    response = client.get(reverse("users:choix_type_utilisateur"))

    assert response.status_code == 200
    assert "form" in response.context
    assert isinstance(response.context["form"], ChoixTypeUtilisateurForm)


@pytest.mark.django_db
@pytest.mark.parametrize("is_conseiller_rse", [True, False])
def test_choix_type_utilisateur_redirige_si_deja_choisi(
    is_conseiller_rse, client, alice
):
    alice.is_conseiller_rse = is_conseiller_rse
    alice.save()
    client.force_login(alice)

    response = client.get(reverse("users:choix_type_utilisateur"))

    assert response.status_code == 302


@pytest.mark.django_db
def test_choix_conseiller_rse_met_a_jour_utilisateur(client, django_user_model):
    """Choisir 'conseiller RSE' met à jour is_conseiller_rse."""
    utilisateur = django_user_model.objects.create(
        email="nouveau@test.fr",
    )
    client.force_login(utilisateur)

    response = client.post(
        reverse("users:choix_type_utilisateur"),
        {
            "type_utilisateur": ChoixTypeUtilisateurForm.TYPE_CONSEILLER_RSE,
            "fonction_rse": "auditeur",
        },
    )

    utilisateur.refresh_from_db()
    assert utilisateur.is_conseiller_rse
    assert utilisateur.fonction_rse == "auditeur"
    assert response.status_code == 302


@pytest.mark.django_db
def test_choix_membre_entreprise_marque_session(client, django_user_model):
    """Choisir 'membre entreprise' marque la session et redirige vers dispatch."""
    utilisateur = django_user_model.objects.create(
        email="nouveau@test.fr",
    )
    client.force_login(utilisateur)

    response = client.post(
        reverse("users:choix_type_utilisateur"),
        {
            "type_utilisateur": ChoixTypeUtilisateurForm.TYPE_MEMBRE_ENTREPRISE,
            "fonction_rse": "",
        },
    )

    assert client.session.get("type_utilisateur_choisi") is True
    assert not utilisateur.fonction_rse
    assert response.status_code == 302
    assert response.url == reverse("users:post_login_dispatch")
