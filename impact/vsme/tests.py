import pytest
from pytest_django.asserts import assertTemplateUsed


@pytest.fixture
def entreprise_qualifiee(entreprise_factory, alice):
    entreprise = entreprise_factory()
    entreprise.users.add(alice)
    return entreprise


def test_acces_vsme_autorise(client, entreprise_qualifiee, alice):
    client.force_login(alice)
    response = client.get(
        f"/vsme/{entreprise_qualifiee.siren}/introduction", follow=True
    )
    assert (
        response.status_code == 200
    ), "Alice doit pouvoir accéder à cette page (membre de l'entreprise)"


def test_acces_vsme_refuse(client, entreprise_qualifiee, bob):
    client.force_login(bob)
    response = client.get(
        f"/vsme/{entreprise_qualifiee.siren}/introduction", follow=True
    )
    assert response.status_code == 403, "Bob ne doit pas pouvoir accéder à cette page"


@pytest.mark.parametrize("etape", ["introduction", "module_base", "module_complet"])
def test_chargement_templates(etape, client, entreprise_qualifiee, alice):
    # vérifie que tous les templates sont bien chargés dans la page résultante
    client.force_login(alice)
    response = client.get(f"/vsme/{entreprise_qualifiee.siren}/{etape}", follow=True)
    assertTemplateUsed(response, "base.html")
    assertTemplateUsed(response, "snippets/entete_page.html")
    assertTemplateUsed(response, "snippets/entete.html")
    assertTemplateUsed(response, "snippets/menu.html")

    # note : pénible black et sa mauvaise gestion du parsing des f-string
    assertTemplateUsed(response, f"etapes/{etape.replace('_','-')}.html")
