from vsme.models import Indicateur
from vsme.tests.test_indicateurs import INDICATEURS_VSME_BASE_URL


def test_indicateur_calculé_affiche_les_donnees_calculées(client, alice, rapport_vsme):
    indicateur_conventions_collectives = "B10-42-c"
    # Indicateur nombre salariés nécessaire pour le calcul du taux de couverture des conventions collectives
    Indicateur.objects.create(
        rapport_vsme=rapport_vsme,
        schema_id="B1-24-e-v",
        data={"methode_comptabilisation": "ETP", "nombre_salaries": 20},
    )
    client.force_login(alice)

    url = (
        INDICATEURS_VSME_BASE_URL
        + f"{rapport_vsme.id}/indicateur/{indicateur_conventions_collectives}/"
    )
    response = client.post(url, {"nombre_salaries_conventions_collectives": 10})

    assert response.status_code == 200
    context = response.context
    content = response.content.decode("utf-8")
    assert (
        context["multiform"].forms[0]["taux_couverture_conventions_collectives"].value()
        == "40-60"
    )  # valeur calculée
    assert "Entre 40 et 60%" in content  # On affiche le label


def test_indicateur_calculé_affiche_na_si_incalculable(client, alice, rapport_vsme):
    indicateur_conventions_collectives = "B10-42-c"
    client.force_login(alice)

    url = (
        INDICATEURS_VSME_BASE_URL
        + f"{rapport_vsme.id}/indicateur/{indicateur_conventions_collectives}/"
    )
    response = client.post(url, {"nombre_salaries_conventions_collectives": 10})

    assert response.status_code == 200
    context = response.context
    content = response.content.decode("utf-8")
    assert (
        context["multiform"].forms[0]["taux_couverture_conventions_collectives"].value()
        == "n/a"
    )  # valeur incalculable sans nombre de salariés renseigné dans B1
    assert "n/a" in content
