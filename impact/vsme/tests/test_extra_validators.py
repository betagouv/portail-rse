from conftest import CODE_SA
from vsme.forms import create_multiform_from_schema
from vsme.models import Indicateur
from vsme.views import load_indicateur_schema


def test_succès_vérification_total_des_salariés(client, rapport_vsme):
    rapport_vsme.entreprise.categorie_juridique_sirene = CODE_SA
    Indicateur.objects.create(
        rapport_vsme=rapport_vsme,
        schema_id="B1-24-e-v",
        data={"methode_comptabilisation": "ETP", "nombre_salaries": 42},
    )
    Indicateur.objects.create(
        rapport_vsme=rapport_vsme,
        schema_id="B1-24-e-vi",
        data={"pays": ["FIN", "FRA"]},
    )
    indicateur_schema = load_indicateur_schema("B8-39-c")
    multiform_class = create_multiform_from_schema(indicateur_schema, rapport_vsme)

    data = {
        "form-TOTAL_FORMS": "2",
        "form-INITIAL_FORMS": "2",
        "form-0-nombre_salaries": "20",
        "form-1-nombre_salaries": "22",
    }
    multiform = multiform_class(data)

    assert multiform.is_valid()


def test_échec_vérification_total_des_salariés(client, rapport_vsme):
    rapport_vsme.entreprise.categorie_juridique_sirene = CODE_SA
    Indicateur.objects.create(
        rapport_vsme=rapport_vsme,
        schema_id="B1-24-e-v",
        data={"methode_comptabilisation": "ETP", "nombre_salaries": 42},
    )
    Indicateur.objects.create(
        rapport_vsme=rapport_vsme,
        schema_id="B1-24-e-vi",
        data={"pays": ["FIN", "FRA"]},
    )
    indicateur_schema = load_indicateur_schema("B8-39-c")
    multiform_class = create_multiform_from_schema(indicateur_schema, rapport_vsme)

    data = {
        "form-TOTAL_FORMS": "2",
        "form-INITIAL_FORMS": "2",
        "form-0-nombre_salaries": "1",
        "form-1-nombre_salaries": "3",
    }
    multiform = multiform_class(data)

    assert not multiform.is_valid()
    assert multiform.forms[0].non_form_errors() == [
        "Le total du nombre de salariés doit être égal à celui indiqué dans l'indicateur de B1 : 42"
    ]
