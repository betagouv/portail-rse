import pytest
from pytest_django.asserts import assertTemplateUsed

INDICATEURS_VSME_URL = "/indicateurs/vsme/{siren}/{annee}/"
CATEGORIE_VSME_URL = "/indicateurs/vsme/{vsme_id}/categorie/{categorie_id}/"


def test_page_indicateurs_vsme(client, entreprise_qualifiee, alice):
    client.force_login(alice)

    url = INDICATEURS_VSME_URL.format(siren=entreprise_qualifiee.siren, annee=2024)
    response = client.get(url)

    assert response.status_code == 200
    assertTemplateUsed(response, "base.html")
    assertTemplateUsed(response, "snippets/tableau_de_bord_menu.html")
    assertTemplateUsed(response, "vsme/indicateurs.html")


@pytest.mark.parametrize(
    "categorie_id", ["informations-generales", "environnement", "social", "gouvernance"]
)
def test_chargement_templates_des_categories_de_vsme(
    categorie_id, client, alice, rapport_vsme
):
    # vérifie que tous les templates sont bien chargés dans la page résultante
    client.force_login(alice)

    url = CATEGORIE_VSME_URL.format(vsme_id=rapport_vsme.id, categorie_id=categorie_id)
    response = client.get(url, follow=True)

    assert response.status_code == 200
    assertTemplateUsed(response, "base.html")
    assertTemplateUsed(response, "snippets/tableau_de_bord_menu.html")
    assertTemplateUsed(response, f"vsme/categorie.html")
    assert response.context["categorie"].value["id"] == categorie_id


def test_categorie_de_vsme_inexistante_retourne_une_404(client, alice, rapport_vsme):
    client.force_login(alice)

    url = CATEGORIE_VSME_URL.format(
        vsme_id=rapport_vsme.id, categorie_id="n-existe-pas"
    )
    response = client.get(url, follow=True)

    assert response.status_code == 404
