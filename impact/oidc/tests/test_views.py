import pytest
from django.conf import settings
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


def test_proconnect_dispatch_view_crée_une_habilitation_editeur_si_proprietaire_déjà_présent(
    client, entreprise_factory, alice_sur_proconnect, bob, carole, mailoutbox
):
    siren = "123456789"
    denomination = "Entreprise de Bob et Carole"
    entreprise = entreprise_factory(siren=siren, denomination=denomination)
    Habilitation.ajouter(entreprise, bob)
    Habilitation.ajouter(entreprise, carole)
    session = client.session
    session["oidc_user_claims"] = {
        "sub": alice_sur_proconnect.oidc_sub_id,
        "siren": siren,
    }
    session.save()
    client.force_login(alice_sur_proconnect)

    response = client.get("/oidc/dispatch/", follow=True)

    habilitation = Habilitation.objects.pour(entreprise, alice_sur_proconnect)
    assert habilitation.role == UserRole.EDITEUR
    assert len(mailoutbox) == 1
    mail = mailoutbox[0]
    assert mail.from_email == settings.DEFAULT_FROM_EMAIL
    assert list(mail.to) == [bob.email, carole.email]
    assert mail.template_id == settings.BREVO_ARRIVEE_NOUVEAU_MEMBRE_TEMPLATE
    assert mail.merge_global_data == {
        "denomination_entreprise": denomination,
        "email_nouveau_membre": alice_sur_proconnect.email,
        "url_administration_entreprise": response.wsgi_request.build_absolute_uri(
            reverse(
                "reglementations:tableau_de_bord",
                kwargs={
                    "siren": entreprise.siren,
                },
            )
        ),
    }
    assert response.status_code == 200
    assert response.redirect_chain[0] == ("/post-login-dispatch", 302)
