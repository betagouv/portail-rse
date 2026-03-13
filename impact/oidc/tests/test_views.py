import pytest
from django.urls import reverse

from entreprises.models import Entreprise
from habilitations.enums import UserRole
from habilitations.models import Habilitation


@pytest.mark.network
def test_proconnect_dispatch_view_cree_l_entreprise_sélectionnée_et_ajoute_l_habilitation(
    client, alice_sur_proconnect, mock_api_infos_entreprise
):
    siren = mock_api_infos_entreprise.return_value["siren"]
    session = client.session
    session["oidc_user_claims"] = {
        "sub": alice_sur_proconnect.oidc_sub_id,
        "siren": siren,
    }
    session.save()
    client.force_login(alice_sur_proconnect)

    response = client.get("/oidc/dispatch/", follow=True)

    entreprise = Entreprise.objects.get(siren=siren)
    habilitation = Habilitation.objects.pour(entreprise, alice_sur_proconnect)
    assert habilitation.role == UserRole.PROPRIETAIRE

    assert response.status_code == 200
    assert response.redirect_chain[0] == ("/post-login-dispatch", 302)
    assert (reverse("users:post_login_dispatch"), 302) in response.redirect_chain


def test_proconnect_dispatch_view_ajoute_l_habilitation_à_l_entreprise_déjà_existante(
    client, entreprise_factory, alice_sur_proconnect
):
    siren = "123456789"
    entreprise = entreprise_factory(siren=siren)
    session = client.session
    session["oidc_user_claims"] = {
        "sub": alice_sur_proconnect.oidc_sub_id,
        "siren": siren,
    }
    session.save()
    client.force_login(alice_sur_proconnect)

    response = client.get("/oidc/dispatch/", follow=True)

    habilitation = Habilitation.objects.pour(entreprise, alice_sur_proconnect)
    assert habilitation.role == UserRole.PROPRIETAIRE
    assert response.status_code == 200
    assert response.redirect_chain[0] == ("/post-login-dispatch", 302)


def test_proconnect_dispatch_view_ne_fait_que_rediriger_si_habilitation_et_entreprise_déjà_existantes(
    client, entreprise_factory, alice_sur_proconnect
):
    siren = "123456789"
    entreprise = entreprise_factory(siren=siren)
    Habilitation.ajouter(entreprise, alice_sur_proconnect)
    session = client.session
    session["oidc_user_claims"] = {
        "sub": alice_sur_proconnect.oidc_sub_id,
        "siren": siren,
    }
    session.save()
    client.force_login(alice_sur_proconnect)

    response = client.get("/oidc/dispatch/", follow=True)

    habilitation = Habilitation.objects.pour(entreprise, alice_sur_proconnect)
    assert habilitation.role == UserRole.PROPRIETAIRE
    assert response.status_code == 200
    assert response.redirect_chain[0] == ("/post-login-dispatch", 302)
