import html
from datetime import date
from datetime import datetime
from datetime import timedelta

import pytest
from django.contrib.messages import WARNING
from django.urls import reverse
from freezegun import freeze_time
from pytest_django.asserts import assertTemplateNotUsed
from pytest_django.asserts import assertTemplateUsed

from habilitations.enums import UserRole
from habilitations.models import Habilitation
from invitations.models import Invitation
from reglementations.views import REGLEMENTATIONS

RESUME_URL = "/tableau-de-bord/{siren}/"
REGLEMENTATIONS_URL = "/tableau-de-bord/{siren}/reglementations/"
RAPPORT_URL = "/tableau-de-bord/{siren}/rapport/"
RESUME_URL_GENERIQUE = "/tableau-de-bord/"
REGLEMENTATIONS_URL_GENERIQUE = "/tableau-de-bord/reglementations/"
RAPPORT_URL_GENERIQUE = "/tableau-de-bord/rapport/"


@pytest.mark.parametrize("url", [RESUME_URL, REGLEMENTATIONS_URL, RAPPORT_URL])
def test_tableau_de_bord_est_prive(url, client, entreprise_factory, alice):
    entreprise = entreprise_factory()

    url = url.format(siren=entreprise.siren)
    response = client.get(url)

    assert response.status_code == 302
    connexion_url = reverse("users:login")
    assert response.url == f"{connexion_url}?next={url}"

    client.force_login(alice)
    response = client.get(url)

    assert response.status_code == 403


@pytest.mark.parametrize("url", [RESUME_URL, REGLEMENTATIONS_URL, RAPPORT_URL])
def test_tableau_de_bord_avec_utilisateur_authentifie(
    url, client, entreprise_factory, alice
):
    entreprise = entreprise_factory(utilisateur=alice)
    client.force_login(alice)

    url = url.format(siren=entreprise.siren)
    response = client.get(url)

    assert response.status_code == 200
    assert response.context["entreprise"] == entreprise


@pytest.mark.parametrize("url", [RESUME_URL, REGLEMENTATIONS_URL])
def test_tableau_de_bord_entreprise_non_qualifiee_redirige_vers_la_qualification(
    url, client, entreprise_non_qualifiee, alice
):
    Habilitation.ajouter(entreprise_non_qualifiee, alice, fonctions="Présidente")
    client.force_login(alice)

    url = url.format(siren=entreprise_non_qualifiee.siren)
    response = client.get(url, follow=True)

    assert response.status_code == 200
    url = f"/entreprises/{entreprise_non_qualifiee.siren}"
    assert response.redirect_chain == [(url, 302)]


@pytest.mark.parametrize("url", [RESUME_URL, REGLEMENTATIONS_URL])
def test_tableau_de_bord_entreprise_qualifiee_dans_le_passe(
    url, client, entreprise_factory, alice
):
    date_cloture_exercice = date(2024, 12, 31)
    entreprise = entreprise_factory(
        utilisateur=alice, date_cloture_exercice=date_cloture_exercice
    )

    url = url.format(siren=entreprise.siren)
    with freeze_time(date_cloture_exercice + timedelta(days=367)):
        client.force_login(alice)
        response = client.get(url)

    assert response.status_code == 200
    content = html.unescape(response.content.decode("utf-8"))
    assert (
        f"Les informations affichées sont basées sur l'exercice comptable {date_cloture_exercice.year}."
        in content
    ), content


@pytest.mark.parametrize("url", [RESUME_URL, REGLEMENTATIONS_URL, RAPPORT_URL])
def test_tableau_de_bord_entreprise_inexistante(url, client, alice):
    client.force_login(alice)

    url = url.format(siren="yolo")
    response = client.get(url)

    assert response.status_code == 404


@pytest.mark.parametrize(
    "url", [RESUME_URL_GENERIQUE, REGLEMENTATIONS_URL_GENERIQUE, RAPPORT_URL_GENERIQUE]
)
def test_tableau_de_bord_sans_siren_redirige_vers_celui_de_l_entreprise_courante(
    url, client, entreprise_factory, alice
):
    entreprise = entreprise_factory(utilisateur=alice)
    client.force_login(alice)

    response = client.get(url)

    assert response.status_code == 302
    assert entreprise.siren in response.url


def test_tableau_de_bord_sans_slash_final(client, entreprise_factory, alice):
    entreprise_factory(utilisateur=alice)
    client.force_login(alice)

    url = "/tableau-de-bord"
    response = client.get(url)

    assert response.status_code == 301
    assert response.url == "/tableau-de-bord/"


@pytest.mark.parametrize(
    "url", [RESUME_URL_GENERIQUE, REGLEMENTATIONS_URL_GENERIQUE, RAPPORT_URL_GENERIQUE]
)
def test_tableau_de_bord_sans_siren_et_sans_entreprise(url, client, alice):
    # Cas limite où un utilisateur n'est rattaché à aucune entreprise
    client.force_login(alice)

    response = client.get(url, follow=True)

    assert response.status_code == 200
    assert response.redirect_chain == [(reverse("entreprises:entreprises"), 302)]
    messages = list(response.context["messages"])
    assert messages[0].level == WARNING
    assert (
        messages[0].message
        == "Commencez par ajouter une entreprise à votre compte utilisateur avant d'accéder à votre tableau de bord."
    )


@pytest.mark.parametrize("est_soumis", [True, False])
def test_tableau_de_bord_resume(est_soumis, client, entreprise_factory, alice, mocker):
    entreprise = entreprise_factory(utilisateur=alice)
    client.force_login(alice)
    for REGLEMENTATION in REGLEMENTATIONS:
        mocker.patch(
            f"{REGLEMENTATION.__module__}.{REGLEMENTATION.__name__}.est_soumis",
            return_value=est_soumis,
        )
    url = RESUME_URL.format(siren=entreprise.siren)

    response = client.get(url)

    assert response.status_code == 200
    assertTemplateUsed(response, "reglementations/tableau_de_bord/resume.html")
    assertTemplateUsed(response, "snippets/contributeurs.html")
    context = response.context
    assert context["entreprise"] == entreprise
    if est_soumis:
        assert context["nombre_reglementations_applicables"] == len(REGLEMENTATIONS)
    else:
        assert context["nombre_reglementations_applicables"] == 0
    assert context["form"]
    assert len(context["habilitations"]) == 1
    assert len(context["invitations"]) == 0


def test_tableau_de_bord_resume_n_affiche_pas_les_utilisateurs_non_confirmés(
    client, alice, bob, entreprise_factory
):
    entreprise = entreprise_factory(utilisateur=alice)
    bob.is_email_confirmed = False
    bob.save()
    Habilitation.ajouter(entreprise, bob, fonctions="Président")
    client.force_login(alice)
    url = RESUME_URL.format(siren=entreprise.siren)

    response = client.get(url)

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert bob.email not in content
    context = response.context
    assert len(context["habilitations"]) == 1


def test_tableau_de_bord_resume_n_affiche_pas_les_invitations_acceptées(
    client, alice, bob, entreprise_factory
):
    entreprise = entreprise_factory(utilisateur=alice)
    Invitation.objects.create(
        email=bob.email, entreprise=entreprise, date_acceptation=datetime.now()
    )
    client.force_login(alice)
    url = RESUME_URL.format(siren=entreprise.siren)

    response = client.get(url)

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert bob.email not in content
    context = response.context
    assert len(context["invitations"]) == 0


@pytest.mark.parametrize(
    "role,resultat", ((UserRole.PROPRIETAIRE, True), (UserRole.EDITEUR, False))
)
def test_visibilite_formulaire_invitation(
    client, bob, entreprise_factory, role, resultat
):
    entreprise = entreprise_factory()
    Habilitation.ajouter(entreprise, bob, role=role)
    client.force_login(bob)
    url = RESUME_URL.format(siren=entreprise.siren)

    response = client.get(url)

    assert response.status_code == 200
    (
        assertTemplateUsed(response, "snippets/formulaire_invitation.html")
        if resultat
        else assertTemplateNotUsed(response, "snippets/formulaire_invitation.html")
    )


@pytest.mark.parametrize(
    "role,resultat", ((UserRole.PROPRIETAIRE, True), (UserRole.EDITEUR, False))
)
def test_visibilite_actions(client, bob, alice, entreprise_factory, role, resultat):
    entreprise = entreprise_factory()
    Habilitation.ajouter(entreprise, bob, role=role)
    Habilitation.ajouter(entreprise, alice, role=UserRole.EDITEUR)
    client.force_login(bob)
    url = RESUME_URL.format(siren=entreprise.siren)

    response = client.get(url)

    assert response.status_code == 200

    if resultat:
        assertTemplateUsed(response, "snippets/modale_modifier_habilitation.html")
        assertTemplateUsed(response, "snippets/modale_retirer_habilitation.html")
    else:
        assertTemplateNotUsed(response, "snippets/modale_modifier_habilitation.html")
        assertTemplateNotUsed(response, "snippets/modale_retirer_habilitation.html")
