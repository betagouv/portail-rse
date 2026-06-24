import pytest
from django.contrib.messages import SUCCESS
from django.urls import reverse


INDICATEUR_SCHEMA_ID = "B1-24-a"
REINITIALISER_INDICATEUR_VSME_URL = (
    "/indicateurs/vsme/{vsme_id}/indicateur/{indicateur_schema_id}/reinitialiser/"
)


def test_reinitialiser_supprime_l_indicateur_et_redirige(client, alice, rapport_vsme):
    rapport_vsme.indicateurs.create(
        schema_id=INDICATEUR_SCHEMA_ID, data={"choix_module": "base"}
    )
    client.force_login(alice)

    url = REINITIALISER_INDICATEUR_VSME_URL.format(
        vsme_id=rapport_vsme.id, indicateur_schema_id=INDICATEUR_SCHEMA_ID
    )
    response = client.post(url, follow=True)

    assert response.status_code == 200
    assert response.redirect_chain == [
        (
            reverse(
                "vsme:exigence_de_publication_vsme",
                kwargs={
                    "vsme_id": rapport_vsme.id,
                    "exigence_de_publication_code": "B1",
                },
            ),
            302,
        )
    ]
    messages = list(response.context["messages"])
    assert messages[0].level == SUCCESS
    assert "réinitialisé" in messages[0].message

    rapport_vsme.refresh_from_db()
    assert not rapport_vsme.indicateurs.filter(schema_id=INDICATEUR_SCHEMA_ID).exists()


def test_reinitialiser_indicateur_non_complete(client, alice, rapport_vsme):
    client.force_login(alice)

    url = REINITIALISER_INDICATEUR_VSME_URL.format(
        vsme_id=rapport_vsme.id, indicateur_schema_id=INDICATEUR_SCHEMA_ID
    )
    response = client.post(url)

    assert response.status_code == 302
    assert response.url == reverse(
        "vsme:exigence_de_publication_vsme",
        kwargs={"vsme_id": rapport_vsme.id, "exigence_de_publication_code": "B1"},
    )


@pytest.mark.parametrize("indicateur_schema_id", ["ZZZ", "B1-ZZZ"])
def test_reinitialiser_indicateur_inexistant_retourne_une_404(
    indicateur_schema_id, client, alice, rapport_vsme
):
    client.force_login(alice)

    url = REINITIALISER_INDICATEUR_VSME_URL.format(
        vsme_id=rapport_vsme.id, indicateur_schema_id=indicateur_schema_id
    )
    response = client.post(url)

    assert response.status_code == 404


def test_reinitialiser_indicateur_d_un_rapport_inexistant_retourne_une_404(
    client, alice
):
    client.force_login(alice)

    url = REINITIALISER_INDICATEUR_VSME_URL.format(
        vsme_id="yolo", indicateur_schema_id=INDICATEUR_SCHEMA_ID
    )
    response = client.post(url)

    assert response.status_code == 404


def test_reinitialiser_indicateur_est_prive(client, bob, rapport_vsme):
    rapport_vsme.indicateurs.create(
        schema_id=INDICATEUR_SCHEMA_ID, data={"choix_module": "base"}
    )

    url = REINITIALISER_INDICATEUR_VSME_URL.format(
        vsme_id=rapport_vsme.id, indicateur_schema_id=INDICATEUR_SCHEMA_ID
    )
    response = client.post(url)

    assert response.status_code == 302
    connexion_url = reverse("users:login")
    assert response.url == f"{connexion_url}?next={url}"

    # Bob n'est pas rattaché à l'entreprise du rapport VSME
    client.force_login(bob)
    response = client.post(url)

    assert response.status_code == 403
