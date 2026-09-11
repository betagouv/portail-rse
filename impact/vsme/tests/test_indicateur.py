import pytest
from django.core.files.base import ContentFile
from django.urls import reverse
from pytest_django.asserts import assertContains
from pytest_django.asserts import assertNotContains
from pytest_django.asserts import assertTemplateUsed

from vsme.tests.test_indicateurs import INDICATEURS_VSME_BASE_URL

INDICATEUR_VSME_URL = INDICATEURS_VSME_BASE_URL + "{vsme_id}/indicateur/B1-24-a/"
INFOS_TROUVEES_IA = "Informations trouvées dans les documents analysés"


def test_indicateur_vsme_htmx_renvoie_le_fragment(client, alice, rapport_vsme):
    client.force_login(alice)

    url = INDICATEUR_VSME_URL.format(vsme_id=rapport_vsme.id)
    response = client.get(url, headers={"HX-Request": "true"})

    assert response.status_code == 200
    assertTemplateUsed(response, "fragments/indicateur.html")


def test_indicateur_vsme_non_htmx_redirige_vers_l_exigence(client, alice, rapport_vsme):
    client.force_login(alice)

    url = INDICATEUR_VSME_URL.format(vsme_id=rapport_vsme.id)
    response = client.get(url)

    assert response.status_code == 302
    assert response.url == reverse(
        "vsme:exigence_de_publication_vsme",
        kwargs={
            "vsme_id": rapport_vsme.id,
            "exigence_de_publication_code": "B1",
        },
    )


@pytest.mark.parametrize("indicateur_schema_id", ["ZZZ", "B1-ZZZ"])
def test_indicateur_vsme_inexistant_retourne_une_404(
    indicateur_schema_id, client, alice, rapport_vsme
):
    client.force_login(alice)

    url = (
        INDICATEURS_VSME_BASE_URL
        + f"{rapport_vsme.id}/indicateur/{indicateur_schema_id}/"
    )
    response = client.get(url)

    assert response.status_code == 404


def test_indicateur_vsme_d_un_rapport_inexistant_retourne_une_404(client, alice):
    client.force_login(alice)

    url = INDICATEUR_VSME_URL.format(vsme_id="yolo")
    response = client.get(url)

    assert response.status_code == 404


def test_indicateur_vsme_est_prive(client, bob, rapport_vsme):
    url = INDICATEUR_VSME_URL.format(vsme_id=rapport_vsme.id)
    response = client.get(url)

    assert response.status_code == 302
    connexion_url = reverse("users:login")
    assert response.url == f"{connexion_url}?next={url}"

    # Bob n'est pas rattaché à l'entreprise du rapport VSME
    client.force_login(bob)
    response = client.get(url)

    assert response.status_code == 403


def test_indicateur_vsme_htmx_non_authentifie_renvoie_hx_redirect(client, rapport_vsme):
    """Évite d'injecter la page de connexion dans la modale et de casser l'affichage"""
    url = INDICATEUR_VSME_URL.format(vsme_id=rapport_vsme.id)
    response = client.get(url, headers={"HX-Request": "true"})

    connexion_url = reverse("users:login")
    assert response.status_code == 200
    assert response["HX-Redirect"] == f"{connexion_url}?next={url}"


def _cree_analyse_ia(rapport_vsme, indicateur_schema_id, champ_id):
    return rapport_vsme.entreprise.analyses_ia.create(
        fichier=ContentFile("pdf file data", name="fichier.pdf"),
        resultat_json_v2={
            indicateur_schema_id: [
                {
                    "champ_id": champ_id,
                    "valeur": "une valeur",
                    "colonne_id": None,
                    "paragraphe": "un paragraphe",
                }
            ]
        },
    )


def test_indicateur_vsme_sans_correspondance_ia_n_affiche_pas_le_bloc(
    client, alice, rapport_vsme
):
    """champ simple : aucun résultat IA ne correspond au champ affiché"""
    _cree_analyse_ia(rapport_vsme, "B1-24-a", champ_id="autre_champ")
    client.force_login(alice)

    url = INDICATEUR_VSME_URL.format(vsme_id=rapport_vsme.id)
    response = client.get(url, headers={"HX-Request": "true"})

    assertNotContains(response, INFOS_TROUVEES_IA)


def test_indicateur_vsme_avec_correspondance_ia_affiche_le_bloc(
    client, alice, rapport_vsme
):
    """champ simple : un résultat IA correspond au champ affiché"""
    _cree_analyse_ia(rapport_vsme, "B1-24-a", champ_id="choix_module")
    client.force_login(alice)

    url = INDICATEUR_VSME_URL.format(vsme_id=rapport_vsme.id)
    response = client.get(url, headers={"HX-Request": "true"})

    assertContains(response, INFOS_TROUVEES_IA)


def test_indicateur_vsme_tableau_sans_correspondance_ia_n_affiche_pas_le_bloc(
    client, alice, rapport_vsme
):
    """tableau : aucun résultat IA ne correspond au champ affiché"""
    _cree_analyse_ia(rapport_vsme, "B1-24-d", champ_id="autre_champ")
    client.force_login(alice)

    url = INDICATEURS_VSME_BASE_URL + f"{rapport_vsme.id}/indicateur/B1-24-d/"
    response = client.get(url, headers={"HX-Request": "true"})

    assertNotContains(response, INFOS_TROUVEES_IA)


def test_indicateur_vsme_tableau_avec_correspondance_ia_affiche_le_bloc(
    client, alice, rapport_vsme
):
    """tableau : un résultat IA correspond au champ affiché"""
    _cree_analyse_ia(rapport_vsme, "B1-24-d", champ_id="filiales")
    client.force_login(alice)

    url = INDICATEURS_VSME_BASE_URL + f"{rapport_vsme.id}/indicateur/B1-24-d/"
    response = client.get(url, headers={"HX-Request": "true"})

    assertContains(response, INFOS_TROUVEES_IA)


def test_indicateur_vsme_bloc_ia_place_juste_au_dessus_du_champ_correspondant(
    client, alice, rapport_vsme
):
    """B1-24-e-v a 2 champs (methode_comptabilisation, nombre_salaries) : le bloc IA du second
    champ doit être positionné entre les deux champs, pas avant l'ensemble du formulaire
    """
    _cree_analyse_ia(rapport_vsme, "B1-24-e-v", champ_id="nombre_salaries")
    client.force_login(alice)

    url = INDICATEURS_VSME_BASE_URL + f"{rapport_vsme.id}/indicateur/B1-24-e-v/"
    response = client.get(url, headers={"HX-Request": "true"})
    contenu = response.content.decode()

    assert 'id="accordion-ia-nombre_salaries"' in contenu
    assert (
        contenu.index('name="methode_comptabilisation"')
        < contenu.index('id="accordion-ia-nombre_salaries"')
        < contenu.index('name="nombre_salaries"')
    )


def test_indicateur_vsme_n_affiche_pas_le_nom_d_un_fichier_sans_correspondance(
    client, alice, rapport_vsme
):
    """champ simple : quand un fichier analysé correspond et un autre non, seul le nom du fichier correspondant est affiché"""
    fichier_correspondant = _cree_analyse_ia(
        rapport_vsme, "B1-24-a", champ_id="choix_module"
    )
    fichier_correspondant.nom = "fichier-correspondant.pdf"
    fichier_correspondant.save()
    fichier_sans_correspondance = _cree_analyse_ia(
        rapport_vsme, "B1-24-a", champ_id="autre_champ"
    )
    fichier_sans_correspondance.nom = "fichier-sans-correspondance.pdf"
    fichier_sans_correspondance.save()
    client.force_login(alice)

    url = INDICATEUR_VSME_URL.format(vsme_id=rapport_vsme.id)
    response = client.get(url, headers={"HX-Request": "true"})

    assertContains(response, "fichier-correspondant.pdf")
    assertNotContains(response, "fichier-sans-correspondance.pdf")
