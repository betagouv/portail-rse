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
    response = client.post(
        url,
        {"nombre_salaries_conventions_collectives": 10},
        headers={"HX-Request": "true"},
    )

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
    response = client.post(
        url,
        {"nombre_salaries_conventions_collectives": 10},
        headers={"HX-Request": "true"},
    )

    assert response.status_code == 200
    context = response.context
    content = response.content.decode("utf-8")
    assert (
        context["multiform"].forms[0]["taux_couverture_conventions_collectives"].value()
        == "n/a"
    )  # valeur incalculable sans nombre de salariés renseigné dans B1
    assert "n/a" in content


def test_estimation_emissions_GES_scopes_1_et_2_calcule_le_total_sans_intensite_GES(
    rapport_vsme,
):
    indicateur = Indicateur.objects.create(
        rapport_vsme=rapport_vsme,
        schema_id="B3-30-p1",
        data={
            "estimation_emissions_GES": {
                "emissions_brutes_GES": {"scope_1": "10", "scope_2_localisation": "5"}
            }
        },
    )

    data = indicateur.data

    assert data["estimation_emissions_GES"]["emissions_brutes_GES"]["total"] == 15
    assert "intensite_GES" not in data


def test_nombre_heures_formation_par_genre_sans_nombre_moyen_calcule(rapport_vsme):
    Indicateur.objects.create(
        rapport_vsme=rapport_vsme,
        schema_id="B8-39-b",
        data={"effectifs_genre": {"homme": {"nombre_salaries": 4}}},
    )
    indicateur = Indicateur.objects.create(
        rapport_vsme=rapport_vsme,
        schema_id="B10-42-d",
        data={
            "nombre_heures_formation_par_genre": {
                "homme": {"total_heures_formation": 10}
            }
        },
    )

    data = indicateur.data

    assert data["nombre_heures_formation_par_genre"]["homme"] == {
        "total_heures_formation": 10
    }
