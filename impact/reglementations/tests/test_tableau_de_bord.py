import html
from datetime import date
from datetime import timedelta

import pytest
from django.contrib.messages import WARNING
from django.urls import reverse
from freezegun import freeze_time

from habilitations.models import Habilitation

RESUME_URL = "/tableau-de-bord/{siren}"
REGLEMENTATIONS_URL = "/tableau-de-bord/{siren}/reglementations"


@pytest.mark.parametrize("url", [RESUME_URL, REGLEMENTATIONS_URL])
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


@pytest.mark.parametrize("url", [RESUME_URL, REGLEMENTATIONS_URL])
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


@pytest.mark.parametrize("url", [RESUME_URL, REGLEMENTATIONS_URL])
def test_tableau_de_bord_entreprise_inexistante(url, client, alice):
    client.force_login(alice)

    url = url.format(siren="yolo")
    response = client.get(url)

    assert response.status_code == 404


def test_tableau_de_bord_sans_siren_redirige_vers_celui_de_l_entreprise_courante(
    client, entreprise_factory, alice
):
    entreprise = entreprise_factory(utilisateur=alice)
    client.force_login(alice)

    url = "/tableau-de-bord"
    response = client.get(url)

    assert response.status_code == 302
    assert response.url == f"/tableau-de-bord/{entreprise.siren}"


def test_tableau_de_bord_sans_siren_et_sans_entreprise(client, alice):
    # Cas limite où un utilisateur n'est rattaché à aucune entreprise
    client.force_login(alice)

    url = "/tableau-de-bord"
    response = client.get(url, follow=True)

    assert response.status_code == 200
    assert response.redirect_chain == [(reverse("entreprises:entreprises"), 302)]
    messages = list(response.context["messages"])
    assert messages[0].level == WARNING
    assert (
        messages[0].message
        == "Commencez par ajouter une entreprise à votre compte utilisateur avant d'accéder à votre tableau de bord"
    )
