import pytest

from vsme.forms import create_multiform_from_schema
from vsme.models import Indicateur
from vsme.views import load_indicateur_schema


@pytest.fixture
def rapport_vsme_42_salariés(rapport_vsme):
    # Indicateur nombre salariés
    Indicateur.objects.create(
        rapport_vsme=rapport_vsme,
        schema_id="B1-24-e-v",
        data={"methode_comptabilisation": "ETP", "nombre_salaries": 42},
    )
    # Indicateur pays
    Indicateur.objects.create(
        rapport_vsme=rapport_vsme,
        schema_id="B1-24-e-vi",
        data={"pays": ["FIN", "FRA"]},
    )
    return rapport_vsme


def test_succès_vérification_total_des_salariés(client, rapport_vsme_42_salariés):
    indicateur_effectifs_pays_schema = load_indicateur_schema("B8-39-c")
    multiform_class = create_multiform_from_schema(
        indicateur_effectifs_pays_schema, rapport_vsme_42_salariés
    )

    data = {
        "effectifs_pays-TOTAL_FORMS": "2",
        "effectifs_pays-INITIAL_FORMS": "2",
        "effectifs_pays-0-nombre_salaries": "20",
        "effectifs_pays-1-nombre_salaries": "22",
        # total nombre salariés égal à 42
    }
    multiform = multiform_class(data)

    assert multiform.is_valid()


def test_échec_vérification_total_des_salariés(client, rapport_vsme_42_salariés):
    indicateur_effectifs_pays_schema = load_indicateur_schema("B8-39-c")
    multiform_class = create_multiform_from_schema(
        indicateur_effectifs_pays_schema, rapport_vsme_42_salariés
    )

    data = {
        "effectifs_pays-TOTAL_FORMS": "2",
        "effectifs_pays-INITIAL_FORMS": "2",
        "effectifs_pays-0-nombre_salaries": "1",
        "effectifs_pays-1-nombre_salaries": "3",
        # total nombre salariés différent de 42
    }
    multiform = multiform_class(data)

    assert not multiform.is_valid()
    assert multiform.forms[0].non_form_errors() == [
        "Le total du nombre de salariés doit être égal à celui indiqué dans l'indicateur de B1 : 42"
    ]


def test_succes_vérification_total_dechets_produit(client, rapport_vsme):
    indicateur_gestion_dechets = load_indicateur_schema("B7-38-ab")
    multiform_class = create_multiform_from_schema(
        indicateur_gestion_dechets, rapport_vsme
    )

    data = {
        "gestion_dechets-TOTAL_FORMS": "1",
        "gestion_dechets-INITIAL_FORMS": "0",
        "gestion_dechets-0-dechet": "01",
        "gestion_dechets-0-dangereux": True,
        "gestion_dechets-0-total_dechets": "3",
        "gestion_dechets-0-recyclage_ou_reutilisation": "1",
        "gestion_dechets-0-elimines": "2",
        # somme recyclage et elimines égale à total_dechets
    }
    multiform = multiform_class(data)
    assert multiform.is_valid()


def test_échec_vérification_total_dechets_produit(client, rapport_vsme):
    indicateur_gestion_dechets = load_indicateur_schema("B7-38-ab")
    multiform_class = create_multiform_from_schema(
        indicateur_gestion_dechets, rapport_vsme
    )

    data = {
        "gestion_dechets-TOTAL_FORMS": "1",
        "gestion_dechets-INITIAL_FORMS": "0",
        "gestion_dechets-0-dechet": "01",
        "gestion_dechets-0-dangereux": True,
        "gestion_dechets-0-total_dechets": "3",
        "gestion_dechets-0-recyclage_ou_reutilisation": "1",
        "gestion_dechets-0-elimines": "4",
        # somme recyclage et elimines différente de total_dechets
    }
    multiform = multiform_class(data)

    assert not multiform.is_valid()
    assert multiform.forms[1].non_form_errors() == [
        "Le total des déchets produits doit être égal à la somme des déchets recyclés et éliminés"
    ]


def test_vérification_total_dechets_produit_non_bloquant_quand_non_pertinent(
    client, rapport_vsme
):
    indicateur_gestion_dechets = load_indicateur_schema("B7-38-ab")
    multiform_class = create_multiform_from_schema(
        indicateur_gestion_dechets, rapport_vsme
    )

    data = {
        "non_pertinent": True,
        "gestion_dechets-TOTAL_FORMS": "1",
        "gestion_dechets-INITIAL_FORMS": "0",
        "gestion_dechets-0-dechet": "01",
        "gestion_dechets-0-dangereux": True,
        "gestion_dechets-0-total_dechets": "3",
        "gestion_dechets-0-recyclage_ou_reutilisation": "1",
        "gestion_dechets-0-elimines": "4",
        # somme recyclage et elimines différente de total_dechets
    }
    multiform = multiform_class(data)

    assert multiform.is_valid()


def test_succes_vérification_total_dechets_produit_nombres_decimaux(
    client, rapport_vsme
):
    indicateur_gestion_dechets = load_indicateur_schema("B7-38-ab")
    multiform_class = create_multiform_from_schema(
        indicateur_gestion_dechets, rapport_vsme
    )

    data = {
        "gestion_dechets-TOTAL_FORMS": "1",
        "gestion_dechets-INITIAL_FORMS": "0",
        "gestion_dechets-0-dechet": "01",
        "gestion_dechets-0-dangereux": True,
        "gestion_dechets-0-total_dechets": "92.13",
        "gestion_dechets-0-recyclage_ou_reutilisation": "0.84",
        "gestion_dechets-0-elimines": "91.29",
        # somme recyclage et elimines égale à total_dechets sauf si les nombres sont de type float
    }
    multiform = multiform_class(data)
    assert multiform.is_valid()
