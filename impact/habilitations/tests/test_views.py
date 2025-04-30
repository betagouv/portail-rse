import html

from django.urls import reverse
from pytest_django.asserts import assertTemplateUsed

from habilitations.models import Habilitation


def test_page_membres_d_une_entreprise(client, alice, entreprise_factory):
    entreprise = entreprise_factory()
    Habilitation.ajouter(entreprise, alice, fonctions="Présidente")
    client.force_login(alice)

    response = client.get(f"/droits/{entreprise.siren}")

    assertTemplateUsed(response, "habilitations/membres.html")
    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert alice.email in content


def test_page_membres_d_une_entreprise_nécessite_d_être_connecté(
    client, alice, entreprise_factory
):
    entreprise = entreprise_factory()
    Habilitation.ajouter(entreprise, alice, fonctions="Présidente")
    url = f"/droits/{entreprise.siren}"

    response = client.get(url, follow=True)

    redirect_url = f"""{reverse("users:login")}?next={url}"""
    assert response.redirect_chain == [(redirect_url, 302)]


def test_invitation_a_devenir_membre(client, alice, entreprise_factory):
    entreprise = entreprise_factory()
    Habilitation.ajouter(entreprise, alice, fonctions="Présidente")
    client.force_login(alice)
    data = {
        "email": "bob@bob.test",
    }
    url = f"/droits/{entreprise.siren}"

    response = client.post(url, data=data, follow=True)

    redirect_url = (
        f"""{reverse("habilitations:membres_entreprise", args=[entreprise.siren])}"""
    )
    assert response.redirect_chain == [(redirect_url, 302)]
    content = html.unescape(response.content.decode("utf-8"))
    assert "L'invitation a été envoyée." in content
