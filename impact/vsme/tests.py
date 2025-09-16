import pytest
from django.contrib.messages import WARNING
from django.urls import reverse
from pytest_django.asserts import assertTemplateUsed


@pytest.fixture
def entreprise_qualifiee(entreprise_factory, alice):
    entreprise = entreprise_factory(utilisateur=alice)
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
def test_chargement_templates_des_etapes_vsme(
    etape, client, entreprise_qualifiee, alice
):
    # vérifie que tous les templates sont bien chargés dans la page résultante
    client.force_login(alice)

    response = client.get(f"/vsme/{entreprise_qualifiee.siren}/{etape}", follow=True)

    assertTemplateUsed(response, "base.html")
    assertTemplateUsed(response, "snippets/entete_page.html")
    assertTemplateUsed(response, "snippets/entete.html")
    assertTemplateUsed(response, "snippets/menu.html")
    assertTemplateUsed(response, f"etapes/{etape.replace("_","-")}.html")


def test_etape_vsme_inexistante_retourne_une_404(client, entreprise_qualifiee, alice):
    client.force_login(alice)

    response = client.get(
        f"/vsme/{entreprise_qualifiee.siren}/n-existe-pas", follow=True
    )

    assert response.status_code == 404


@pytest.mark.parametrize("etape", ["introduction", "module_base", "module_complet"])
def test_siren_absent_redirige_vers_celui_de_l_entreprise_courante(
    etape, client, entreprise_factory, alice
):
    entreprise = entreprise_factory(utilisateur=alice)
    client.force_login(alice)
    url = f"/vsme/{etape}/"

    response = client.get(url, follow=True)

    assert response.status_code == 200
    redirect_url = reverse("vsme:etape_vsme", args=[entreprise.siren, etape])
    assert response.redirect_chain == [(redirect_url, 302)]


@pytest.mark.parametrize("etape", ["introduction", "module_base", "module_complet"])
def test_siren_absent_redirige_vers_l_ajout_d_entreprise_si_pas_d_entreprise(
    etape, client, alice
):
    client.force_login(alice)
    url = f"/vsme/{etape}/"

    response = client.get(url, follow=True)

    assert response.status_code == 200
    assert response.redirect_chain == [(reverse("entreprises:entreprises"), 302)]
    messages = list(response.context["messages"])
    assert messages[0].level == WARNING
    assert (
        messages[0].message
        == "Commencez par ajouter une entreprise à votre compte utilisateur avant d'accéder à l'espace VSME"
    )


def test_page_indicateurs_vsme(client, entreprise_qualifiee, alice):
    client.force_login(alice)

    response = client.get(f"/indicateurs/{entreprise_qualifiee.siren}")

    assertTemplateUsed(response, "base.html")
    assertTemplateUsed(response, "snippets/tableau_de_bord_menu.html")
    assertTemplateUsed(response, "vsme/indicateurs.html")


@pytest.mark.parametrize(
    "categorie", ["informations-generales", "environnement", "social", "gouvernance"]
)
def test_chargement_templates_des_categories_de_vsme(
    categorie, client, entreprise_qualifiee, alice
):
    # vérifie que tous les templates sont bien chargés dans la page résultante
    client.force_login(alice)

    response = client.get(
        f"/indicateurs/{entreprise_qualifiee.siren}/{categorie}", follow=True
    )

    assertTemplateUsed(response, "base.html")
    assertTemplateUsed(response, "snippets/tableau_de_bord_menu.html")
    assertTemplateUsed(response, f"categories/{categorie}.html")


@pytest.mark.parametrize(
    "categorie", ["informations-generales", "environnement", "social", "gouvernance"]
)
def test_categorie_de_vsme(categorie, client, entreprise_qualifiee, alice):
    # vérifie que tous les templates sont bien chargés dans la page résultante
    client.force_login(alice)

    response = client.get(f"/indicateurs/{entreprise_qualifiee.siren}/{categorie}")

    assertTemplateUsed(response, "base.html")
    assertTemplateUsed(response, "snippets/tableau_de_bord_menu.html")
    assertTemplateUsed(response, f"categories/{categorie}.html")


def test_categorie_de_vsme_inexistante_retourne_une_404(
    client, entreprise_qualifiee, alice
):
    # vérifie que tous les templates sont bien chargés dans la page résultante
    client.force_login(alice)

    response = client.get(
        f"/indicateurs/{entreprise_qualifiee.siren}/n-existe-pas", follow=True
    )

    assert response.status_code == 404
