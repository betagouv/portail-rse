import pytest
from django.urls import reverse

from poc_lee.models import PreremplissageLee
from poc_lee.tests.conftest import JETON
from vsme.models import Indicateur
from vsme.models import RapportVSME

URL = "/poc-lee/entreprises/045850617/vsme/preremplissages"

CORPS = {
    "annee": 2025,
    "pratiques": [
        {
            "thematique": "personnel",
            "description": "Nous accueillons deux alternants par an.",
        },
        {
            "thematique": "communautes",
            "description": "Nous recevons des élèves de 3e en stage.",
        },
    ],
}


def envoie(client, corps):
    return client.post(
        URL,
        data=corps,
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {JETON}",
    )


def donnees_par_schema(rapport):
    return {
        p.schema_id: p.data
        for p in PreremplissageLee.objects.filter(rapport_vsme=rapport)
    }


def test_cree_le_rapport_et_les_preremplissages(client, poc_actif, tpe_commerce):
    response = envoie(client, CORPS)

    assert response.status_code == 201
    rapport = RapportVSME.objects.get(entreprise=tpe_commerce, annee=2025)
    assert response.json() == {
        "rapport_url": "http://testserver"
        + reverse("vsme:exigence_de_publication_vsme", args=[rapport.id, "B2"])
    }
    assert donnees_par_schema(rapport) == {
        "B2-26": {
            "declaration_durabilite": {
                "personnel": {"pratiques": True},
                "communautes": {"pratiques": True},
            }
        },
        "C2-48": {
            "description_durabilite": {
                "personnel": {
                    "description_pratiques": "Nous accueillons deux alternants par an."
                },
                "communautes": {
                    "description_pratiques": "Nous recevons des élèves de 3e en stage."
                },
            }
        },
    }


def test_un_second_envoi_remplace_le_premier(client, poc_actif, tpe_commerce):
    envoie(client, CORPS)
    envoie(
        client,
        {
            "annee": 2025,
            "pratiques": [
                {"thematique": "travailleurs", "description": "Achats inclusifs."}
            ],
        },
    )

    rapport = RapportVSME.objects.get(entreprise=tpe_commerce, annee=2025)
    assert donnees_par_schema(rapport) == {
        "B2-26": {"declaration_durabilite": {"travailleurs": {"pratiques": True}}},
        "C2-48": {
            "description_durabilite": {
                "travailleurs": {"description_pratiques": "Achats inclusifs."}
            }
        },
    }


def test_n_ecrit_jamais_dans_les_indicateurs(client, poc_actif, tpe_commerce):
    avant = Indicateur.objects.count()

    envoie(client, CORPS)

    assert Indicateur.objects.count() == avant


@pytest.mark.parametrize(
    "corps",
    [
        {"annee": 2025, "pratiques": [{"thematique": "inconnue", "description": "x"}]},
        {"annee": 2025, "pratiques": [{"thematique": "personnel", "description": " "}]},
        {
            "annee": 2025,
            "pratiques": [
                {"thematique": "personnel", "description": "a"},
                {"thematique": "personnel", "description": "b"},
            ],
        },
        {"annee": 2025, "pratiques": []},
        {"pratiques": [{"thematique": "personnel", "description": "a"}]},
    ],
)
def test_refuse_une_requete_invalide(client, poc_actif, tpe_commerce, corps):
    response = envoie(client, corps)

    assert response.status_code == 400
    assert response.json() == {"erreur": "requete-invalide"}
    assert not RapportVSME.objects.filter(entreprise=tpe_commerce).exists()


def test_refuse_un_jeton_invalide(client, poc_actif, tpe_commerce):
    response = client.post(
        URL,
        data=CORPS,
        content_type="application/json",
        HTTP_AUTHORIZATION="Bearer faux",
    )

    assert response.status_code == 401
