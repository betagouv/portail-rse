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
        "form-TOTAL_FORMS": "2",
        "form-INITIAL_FORMS": "2",
        "form-0-nombre_salaries": "20",
        "form-1-nombre_salaries": "22",
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
        "form-TOTAL_FORMS": "2",
        "form-INITIAL_FORMS": "2",
        "form-0-nombre_salaries": "1",
        "form-1-nombre_salaries": "3",
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
        "form-TOTAL_FORMS": "1",
        "form-INITIAL_FORMS": "0",
        "form-0-dechet": "01",
        "form-0-total_dechets": "3",
        "form-0-recyclage_ou_reutilisation": "1",
        "form-0-elimines": "2",
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
        "form-TOTAL_FORMS": "1",
        "form-INITIAL_FORMS": "0",
        "form-0-dechet": "01",
        "form-0-total_dechets": "3",
        "form-0-recyclage_ou_reutilisation": "1",
        "form-0-elimines": "4",
        # somme recyclage et elimines différente de total_dechets
    }
    multiform = multiform_class(data)

    assert not multiform.is_valid()
    assert multiform.forms[1].non_form_errors() == [
        "Le total des déchets produits doit être égal à la somme des déchets recyclés et éliminés"
    ]
