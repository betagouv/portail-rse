import pytest
from django.urls import reverse
from pytest_django.asserts import assertTemplateUsed

from vsme.models import EXIGENCES_DE_PUBLICATION

INDICATEURS_VSME_BASE_URL = "/indicateurs/vsme/"
INDICATEURS_VSME_URL = INDICATEURS_VSME_BASE_URL + "{siren}/{annee}/"
CATEGORIE_VSME_URL = INDICATEURS_VSME_BASE_URL + "{vsme_id}/categorie/{categorie_id}/"
EXIGENCE_DE_PUBLICATION_URL = (
    INDICATEURS_VSME_BASE_URL
    + "{vsme_id}/exigence-de-publication/{exigence_de_publication_code}/"
)


def test_categories_vsme_est_prive(client, entreprise_factory, alice):
    entreprise = entreprise_factory()

    url = INDICATEURS_VSME_URL.format(siren=entreprise.siren, annee=2024)
    response = client.get(url)

    assert response.status_code == 302
    connexion_url = reverse("users:login")
    assert response.url == f"{connexion_url}?next={url}"

    client.force_login(alice)
    response = client.get(url)

    assert response.status_code == 403


def test_categories_vsme_avec_utilisateur_authentifie(
    client, entreprise_factory, alice
):
    entreprise = entreprise_factory(utilisateur=alice)
    client.force_login(alice)

    url = INDICATEURS_VSME_URL.format(siren=entreprise.siren, annee=2024)
    response = client.get(url)

    assert response.status_code == 200
    assertTemplateUsed(response, "base.html")
    assertTemplateUsed(response, "snippets/tableau_de_bord_menu.html")
    assertTemplateUsed(response, "vsme/categories.html")


def test_categories_vsme_sans_siren_et_sans_annee(client, entreprise_factory, alice):
    entreprise = entreprise_factory(utilisateur=alice)
    client.force_login(alice)

    url = INDICATEURS_VSME_BASE_URL
    response = client.get(url, follow=True)

    assert response.status_code == 200
    assert response.redirect_chain == [(f"/indicateurs/vsme/{entreprise.siren}/", 302)]


@pytest.mark.parametrize(
    "categorie_id", ["informations-generales", "environnement", "social", "gouvernance"]
)
def test_categorie_vsme_avec_utilisateur_authentifie(
    categorie_id, client, alice, rapport_vsme
):
    client.force_login(alice)

    url = CATEGORIE_VSME_URL.format(vsme_id=rapport_vsme.id, categorie_id=categorie_id)
    response = client.get(url)

    assert response.status_code == 200
    # vérifie que tous les templates sont bien chargés dans la page résultante
    assertTemplateUsed(response, "base.html")
    assertTemplateUsed(response, "snippets/tableau_de_bord_menu.html")
    assertTemplateUsed(response, f"vsme/categorie.html")
    assert response.context["categorie"].value["id"] == categorie_id


def test_categorie_vsme_inexistante_retourne_une_404(client, alice, rapport_vsme):
    client.force_login(alice)

    url = CATEGORIE_VSME_URL.format(
        vsme_id=rapport_vsme.id, categorie_id="n-existe-pas"
    )
    response = client.get(url)

    assert response.status_code == 404


def test_categorie_vsme_d_un_rapport_inexistant_retourne_une_404(client, alice):
    client.force_login(alice)

    url = CATEGORIE_VSME_URL.format(vsme_id="yolo", categorie_id="environnement")

    response = client.get(url)

    assert response.status_code == 404


def test_categorie_vsme_est_privee(client, bob, rapport_vsme):
    url = CATEGORIE_VSME_URL.format(
        vsme_id=rapport_vsme.id, categorie_id="environnement"
    )
    response = client.get(url)

    assert response.status_code == 302
    connexion_url = reverse("users:login")
    assert response.url == f"{connexion_url}?next={url}"

    # Bob n'est pas rattaché à l'entreprise du rapport VSME
    client.force_login(bob)
    response = client.get(url)

    assert response.status_code == 403


EXIGENCES_DE_PUBLICATION_REMPLISSABLES = [
    e for code, e in EXIGENCES_DE_PUBLICATION.items() if e.remplissable
]


@pytest.mark.parametrize(
    "exigence_de_publication", EXIGENCES_DE_PUBLICATION_REMPLISSABLES
)
def test_exigence_de_publication_vsme_avec_utilisateur_authentifie(
    exigence_de_publication, client, alice, rapport_vsme
):
    client.force_login(alice)

    url = EXIGENCE_DE_PUBLICATION_URL.format(
        vsme_id=rapport_vsme.id,
        exigence_de_publication_code=exigence_de_publication.code,
    )
    response = client.get(url)

    assert response.status_code == 200
    # vérifie que tous les templates sont bien chargés dans la page résultante
    assertTemplateUsed(response, "base.html")
    assertTemplateUsed(response, "snippets/tableau_de_bord_menu.html")
    assertTemplateUsed(response, f"vsme/exigence_de_publication.html")
    assert response.context["exigence_de_publication"] == exigence_de_publication


def test_exigence_de_publication_vsme_inexistante_retourne_une_404(
    client, alice, rapport_vsme
):
    client.force_login(alice)

    url = EXIGENCE_DE_PUBLICATION_URL.format(
        vsme_id=rapport_vsme.id, exigence_de_publication_code="Z1"
    )
    response = client.get(url)

    assert response.status_code == 404


def test_exigence_de_publication_vsme_d_un_rapport_inexistant_retourne_une_404(
    client, alice
):
    client.force_login(alice)

    url = EXIGENCE_DE_PUBLICATION_URL.format(
        vsme_id="yolo", exigence_de_publication_code="B1"
    )

    response = client.get(url)

    assert response.status_code == 404


def test_exigence_de_publication_vsme_est_privee(client, bob, rapport_vsme):
    url = EXIGENCE_DE_PUBLICATION_URL.format(
        vsme_id=rapport_vsme.id, exigence_de_publication_code="B1"
    )
    response = client.get(url)

    assert response.status_code == 302
    connexion_url = reverse("users:login")
    assert response.url == f"{connexion_url}?next={url}"

    # Bob n'est pas rattaché à l'entreprise du rapport VSME
    client.force_login(bob)
    response = client.get(url)

    assert response.status_code == 403
