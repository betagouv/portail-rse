import pytest
from django.urls import reverse
from pytest_django.asserts import assertTemplateUsed

from habilitations.models import Habilitation

INDICATEURS_VSME_BASE_URL = "/indicateurs/vsme/"
INDICATEURS_VSME_URL = INDICATEURS_VSME_BASE_URL + "{siren}/{annee}/"
CATEGORIE_VSME_URL = INDICATEURS_VSME_BASE_URL + "{vsme_id}/categorie/{categorie_id}/"


def test_indicateurs_vsme_est_prive(client, entreprise_factory, alice):
    entreprise = entreprise_factory()

    url = INDICATEURS_VSME_URL.format(siren=entreprise.siren, annee=2024)
    response = client.get(url)

    assert response.status_code == 302
    connexion_url = reverse("users:login")
    assert response.url == f"{connexion_url}?next={url}"

    client.force_login(alice)
    response = client.get(url)

    assert response.status_code == 403


def test_indicateurs_vsme_avec_utilisateur_authentifie(
    client, entreprise_qualifiee, alice
):
    client.force_login(alice)

    url = INDICATEURS_VSME_URL.format(siren=entreprise_qualifiee.siren, annee=2024)
    response = client.get(url)

    assert response.status_code == 200
    assertTemplateUsed(response, "base.html")
    assertTemplateUsed(response, "snippets/tableau_de_bord_menu.html")
    assertTemplateUsed(response, "vsme/indicateurs.html")


def test_indicateurs_vsme_entreprise_non_qualifiee_redirige_vers_la_qualification(
    client, entreprise_non_qualifiee, alice
):
    Habilitation.ajouter(entreprise_non_qualifiee, alice, fonctions="Présidente")
    client.force_login(alice)

    url = INDICATEURS_VSME_URL.format(siren=entreprise_non_qualifiee.siren, annee=2024)
    response = client.get(url, follow=True)

    assert response.status_code == 200
    url = f"/entreprises/{entreprise_non_qualifiee.siren}"
    assert response.redirect_chain == [(url, 302)]


def test_indicateurs_vsme_sans_siren_et_sans_annee(client, entreprise_qualifiee, alice):
    client.force_login(alice)

    url = INDICATEURS_VSME_BASE_URL
    response = client.get(url, follow=True)

    assert response.status_code == 200
    assert response.redirect_chain == [
        (f"/indicateurs/vsme/{entreprise_qualifiee.siren}/", 302)
    ]


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
