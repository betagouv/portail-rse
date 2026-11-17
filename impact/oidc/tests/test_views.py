import html
from uuid import uuid4

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

    entreprise = Entreprise.objects.get(code_pays="FRA", identifiant=siren)
    habilitation = Habilitation.objects.pour(entreprise, alice_sur_proconnect)
    assert habilitation.role == UserRole.ADMINISTRATEUR

    assert response.status_code == 200
    assert response.redirect_chain[0] == ("/post-login-dispatch", 302)
    assert (reverse("users:post_login_dispatch"), 302) in response.redirect_chain


def test_proconnect_dispatch_view_ajoute_l_habilitation_à_l_entreprise_déjà_existante(
    client, entreprise_factory, alice_sur_proconnect
):
    siren = "123456789"
    entreprise = entreprise_factory(identifiant=siren)
    session = client.session
    session["oidc_user_claims"] = {
        "sub": alice_sur_proconnect.oidc_sub_id,
        "siren": siren,
    }
    session.save()
    client.force_login(alice_sur_proconnect)

    response = client.get("/oidc/dispatch/", follow=True)

    habilitation = Habilitation.objects.pour(entreprise, alice_sur_proconnect)
    assert habilitation.role == UserRole.ADMINISTRATEUR
    assert response.status_code == 200
    assert response.redirect_chain[0] == ("/post-login-dispatch", 302)


def test_proconnect_dispatch_view_ne_fait_que_rediriger_si_habilitation_et_entreprise_déjà_existantes(
    client, entreprise_factory, alice_sur_proconnect
):
    siren = "123456789"
    entreprise = entreprise_factory(identifiant=siren)
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
    assert habilitation.role == UserRole.ADMINISTRATEUR
    assert response.status_code == 200
    assert response.redirect_chain[0] == ("/post-login-dispatch", 302)


def test_proconnect_dispatch_view_crée_une_habilitation_contributeur_si_administrateur_déjà_présent(
    client, entreprise_factory, alice_sur_proconnect, bob, carole, mailoutbox
):
    siren = "123456789"
    denomination = "Entreprise de Bob et Carole"
    entreprise = entreprise_factory(identifiant=siren, denomination=denomination)
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
    assert habilitation.role == UserRole.CONTRIBUTEUR
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
                "tableau_de_bord:resume",
                kwargs={
                    "id_public": entreprise.id_public,
                },
            )
        ),
    }
    assert response.status_code == 200
    assert response.redirect_chain[0] == ("/post-login-dispatch", 302)


def test_proconnect_dispatch_view_n_ajoute_pas_un_compte_etranger_a_une_entreprise_francaise_existante(
    client, entreprise_factory, alice_sur_proconnect
):
    alice_sur_proconnect.est_francais = False
    alice_sur_proconnect.save()
    siren = "123456789"
    entreprise = entreprise_factory(identifiant=siren)
    session = client.session
    session["oidc_user_claims"] = {
        "sub": alice_sur_proconnect.oidc_sub_id,
        "siren": siren,
    }
    session.save()
    client.force_login(alice_sur_proconnect)

    response = client.get("/oidc/dispatch/", follow=True)

    assert not Habilitation.existe(entreprise, alice_sur_proconnect)
    assert response.redirect_chain[0] == (settings.LOGIN_REDIRECT_URL, 302)
    content = html.unescape(response.content.decode("utf-8"))
    assert (
        "Un compte étranger ne peut pas être membre d'une entreprise française."
        in content
    )


def test_proconnect_dispatch_view_n_ajoute_pas_un_compte_etranger_a_une_nouvelle_entreprise_francaise(
    client, alice_sur_proconnect, mock_api_infos_entreprise
):
    alice_sur_proconnect.est_francais = False
    alice_sur_proconnect.save()
    siren = mock_api_infos_entreprise.return_value["siren"]
    session = client.session
    session["oidc_user_claims"] = {
        "sub": alice_sur_proconnect.oidc_sub_id,
        "siren": siren,
    }
    session.save()
    client.force_login(alice_sur_proconnect)

    response = client.get("/oidc/dispatch/", follow=True)

    assert not alice_sur_proconnect.entreprises
    assert response.redirect_chain[0] == (settings.LOGIN_REDIRECT_URL, 302)
    content = html.unescape(response.content.decode("utf-8"))
    assert (
        "Un compte étranger ne peut pas être membre d'une entreprise française."
        in content
    )


def test_proconnect_dispatch_view_repasse_en_francais_un_compte_etranger_non_confirme(
    client, entreprise_factory, alice
):
    # compte étranger créé par un tiers avec l'e-mail d'alice, jamais confirmé
    alice.est_francais = False
    alice.is_email_confirmed = False
    alice.set_password("Passw0rd!123")
    alice.oidc_sub_id = str(uuid4())
    alice.save()
    siren = "123456789"
    entreprise = entreprise_factory(identifiant=siren)
    session = client.session
    session["oidc_user_claims"] = {"sub": alice.oidc_sub_id, "siren": siren}
    session.save()
    client.force_login(alice)

    response = client.get("/oidc/dispatch/", follow=True)

    alice.refresh_from_db()
    assert alice.est_francais
    assert alice.is_email_confirmed
    assert not alice.has_usable_password()
    assert response.context["user"].is_authenticated
    assert Habilitation.existe(entreprise, alice)


def test_proconnect_dispatch_view_ne_repasse_pas_en_francais_un_compte_etranger_confirme(
    client, entreprise_factory, alice_sur_proconnect
):
    alice_sur_proconnect.est_francais = False
    alice_sur_proconnect.save()
    siren = "123456789"
    entreprise_factory(identifiant=siren)
    session = client.session
    session["oidc_user_claims"] = {
        "sub": alice_sur_proconnect.oidc_sub_id,
        "siren": siren,
    }
    session.save()
    client.force_login(alice_sur_proconnect)

    client.get("/oidc/dispatch/", follow=True)

    alice_sur_proconnect.refresh_from_db()
    assert alice_sur_proconnect.est_etranger
