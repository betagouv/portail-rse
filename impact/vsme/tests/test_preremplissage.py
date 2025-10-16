from conftest import CODE_SA
from vsme.tests.test_indicateurs import INDICATEURS_VSME_BASE_URL
from vsme.views import preremplit_indicateur


def test_preremplit_indicateur_qu_on_ne_sait_pas_preremplir(rapport_vsme):
    indicateur_schema_id = "B1-24-a"  # indicateur choix module

    preremplissage = preremplit_indicateur(indicateur_schema_id, rapport_vsme)

    assert preremplissage == {}


def test_preremplit_indicateur_forme_juridique(rapport_vsme):
    rapport_vsme.entreprise.categorie_juridique_sirene = CODE_SA
    indicateur_schema_id = "B1-24-e-i"

    preremplissage = preremplit_indicateur(indicateur_schema_id, rapport_vsme)

    assert preremplissage == {
        "initial": {
            "forme_juridique": "55",
            "coopérative": False,
        },
        "source": {
            "nom": "l'Annuaire des Entreprise",
            "url": "https://annuaire-entreprises.data.gouv.fr/",
        },
    }


def test_indicateur_prerempli_affiche_le_preremplissage(client, alice, rapport_vsme):
    rapport_vsme.entreprise.categorie_juridique_sirene = CODE_SA
    client.force_login(alice)

    url = INDICATEURS_VSME_BASE_URL + f"{rapport_vsme.id}/indicateur/B1-24-e-i/"
    response = client.get(url)

    assert response.status_code == 200
    context = response.context
    content = response.content.decode("utf-8")
    assert "Annuaire des Entreprise" in content, content
    assert context["multiform"].forms[0]["forme_juridique"].value() == "55"
