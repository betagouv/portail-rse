import pytest

from vsme.forms import create_multiform_from_schema

CHAMP_NOM = {
    "id": "nom",
    "label": "Nom",
    "type": "texte",
    "obligatoire": True,
}

CHAMP_AGE = {
    "id": "age",
    "label": "Âge",
    "type": "nombre_entier",
    "unité": "ans",
}

TABLEAU_EMPLOYES = {
    "id": "employes",
    "label": "Employés",
    "type": "tableau",
    "colonnes": [
        {
            "id": "nom_employe",
            "label": "Nom",
            "type": "texte",
            "obligatoire": True,
        },
        {
            "id": "fonction",
            "label": "Fonction",
            "type": "texte",
        },
    ],
}


TABLEAU_REPARTITION_HOMME_FEMME = {
    "id": "repartition",
    "label": "Répartition par genre",
    "type": "tableau_lignes_fixes",
    "colonnes": [
        {
            "id": "nombre_heures_travaillees",
            "label": "Nombre d'heures travaillées",
            "type": "nombre_decimal",
        },
        {
            "id": "representation_conseil_administration",
            "label": "Est représenté au conseil d'administration",
            "type": "choix_binaire_radio",
        },
    ],
    "lignes": [
        {"id": "homme", "label": "Homme"},
        {"id": "femme", "label": "Femme"},
        {"id": "autre", "label": "Autre"},
    ],
}


@pytest.fixture
def indicateur_avec_champs_simples():
    return {
        "schema_id": "TEST-1",
        "titre": "Test simple",
        "description": "Description test",
        "ancre": "test",
        "champs": [CHAMP_NOM, CHAMP_AGE],
    }


@pytest.fixture
def indicateur_avec_tableau():
    return {
        "schema_id": "TEST-2",
        "titre": "Test tableau",
        "description": "Description test",
        "ancre": "test",
        "champs": [TABLEAU_EMPLOYES],
    }


@pytest.fixture
def indicateur_si_pertinent():
    return {
        "schema_id": "TEST-3",
        "titre": "Test si pertinent",
        "description": "Description test",
        "ancre": "test",
        "si_pertinent": True,
        "champs": [CHAMP_AGE],
    }


@pytest.fixture
def indicateur_champs_et_tableau():
    return {
        "schema_id": "TEST-4",
        "titre": "Test champs + tableau",
        "description": "Description test",
        "ancre": "test",
        "champs": [
            CHAMP_NOM,
            TABLEAU_EMPLOYES,
            {
                "id": "commentaire",
                "label": "Commentaire",
                "type": "texte",
            },
        ],
    }


@pytest.fixture
def indicateur_avec_tableau_lignes_fixes():
    return {
        "schema_id": "TEST-5",
        "titre": "Test tableau lignes fixes",
        "description": "Description test",
        "ancre": "test",
        "champs": [TABLEAU_REPARTITION_HOMME_FEMME],
    }


def test_create_multiform_from_schema_avec_champs_simples(
    indicateur_avec_champs_simples,
):
    multiform_class = create_multiform_from_schema(indicateur_avec_champs_simples)

    assert multiform_class.Forms
    assert len(multiform_class.Forms) == 1
    form = multiform_class.Forms[0]
    assert "nom" in form.base_fields
    assert "age" in form.base_fields


def test_create_multiform_from_schema_avec_tableau(indicateur_avec_tableau):
    multiform_class = create_multiform_from_schema(indicateur_avec_tableau)

    assert multiform_class.Forms
    assert len(multiform_class.Forms) == 1
    formset = multiform_class.Forms[0]
    assert formset.id == "employes"


def test_create_multiform_from_schema_si_pertinent(indicateur_si_pertinent):
    multiform_class = create_multiform_from_schema(
        indicateur_si_pertinent, toggle_pertinent_url="/test/"
    )

    assert multiform_class.si_pertinent is True
    assert len(multiform_class.Forms) == 1
    form = multiform_class.Forms[0]
    assert "non_pertinent" in form.base_fields
    assert "age" in form.base_fields


def test_multiform_validation_champs_simples(indicateur_avec_champs_simples):
    multiform_class = create_multiform_from_schema(indicateur_avec_champs_simples)
    multiform = multiform_class({"nom": "Alice", "age": 30})

    assert multiform.is_valid()
    assert multiform.cleaned_data["nom"] == "Alice"
    assert multiform.cleaned_data["age"] == 30


def test_multiform_validation_champ_obligatoire_manquant(
    indicateur_avec_champs_simples,
):
    multiform_class = create_multiform_from_schema(indicateur_avec_champs_simples)
    multiform = multiform_class({"age": 30})

    assert not multiform.is_valid()
    assert "Ce champ est obligatoire." in multiform.forms[0].errors["nom"]


def test_multiform_validation_tableau(indicateur_avec_tableau):
    multiform_class = create_multiform_from_schema(indicateur_avec_tableau, extra=1)
    data = {
        "form-TOTAL_FORMS": "1",
        "form-INITIAL_FORMS": "0",
        "form-0-nom_employe": "Alice",
        "form-0-fonction": "Présidente",
    }
    multiform = multiform_class(data)

    assert multiform.is_valid()
    assert len(multiform.cleaned_data["employes"]) == 1
    assert multiform.cleaned_data["employes"][0] == {
        "nom_employe": "Alice",
        "fonction": "Présidente",
    }


def test_multiform_tableau_suppression_ligne(indicateur_avec_tableau):
    multiform_class = create_multiform_from_schema(indicateur_avec_tableau, extra=0)
    data = {
        "form-TOTAL_FORMS": "3",
        "form-INITIAL_FORMS": "2",
        "form-0-nom_employe": "Alice",
        "form-0-fonction": "Présidente",
        "form-1-nom_employe": "Bob",
        "form-1-fonction": "Associé",
        "form-1-DELETE": "on",
        "form-2-nom_employe": "Charlie",
        "form-2-fonction": "Responsable RSE",
    }
    multiform = multiform_class(data)

    assert multiform.is_valid()
    assert len(multiform.cleaned_data["employes"]) == 2
    employes = multiform.cleaned_data["employes"]
    assert employes[0] == {"nom_employe": "Alice", "fonction": "Présidente"}
    assert employes[1] == {"nom_employe": "Charlie", "fonction": "Responsable RSE"}


def test_multiform_tableau_minimum_une_ligne_requise(indicateur_avec_tableau):
    multiform_class = create_multiform_from_schema(indicateur_avec_tableau, extra=0)
    data = {
        "form-TOTAL_FORMS": "0",
        "form-INITIAL_FORMS": "0",
    }
    multiform = multiform_class(data)

    assert not multiform.is_valid()
    assert (
        "Le tableau doit contenir au moins une ligne."
        in multiform.forms[0].non_form_errors()
    )


def test_multiform_champs_avant_et_apres_tableau(indicateur_champs_et_tableau):
    multiform_class = create_multiform_from_schema(
        indicateur_champs_et_tableau, extra=1
    )

    assert len(multiform_class.Forms) == 3
    form_avant = multiform_class.Forms[0]
    formset = multiform_class.Forms[1]
    form_apres = multiform_class.Forms[2]

    assert "nom" in form_avant.base_fields
    assert formset.id == "employes"
    assert "commentaire" in form_apres.base_fields


def test_multiform_champs_et_tableau_validation(indicateur_champs_et_tableau):
    multiform_class = create_multiform_from_schema(
        indicateur_champs_et_tableau, extra=1
    )
    data = {
        "nom": "Alice",
        "form-TOTAL_FORMS": "1",
        "form-INITIAL_FORMS": "0",
        "form-0-nom_employe": "Charlie",
        "form-0-fonction": "Responsable RSE",
        "commentaire": "Test",
    }
    multiform = multiform_class(data)

    assert multiform.is_valid()
    assert multiform.cleaned_data["nom"] == "Alice"
    assert multiform.cleaned_data["employes"][0]["nom_employe"] == "Charlie"
    assert multiform.cleaned_data["commentaire"] == "Test"


def test_multiform_si_pertinent_non_pertinent_desactive_champs(indicateur_si_pertinent):
    multiform_class = create_multiform_from_schema(
        indicateur_si_pertinent, toggle_pertinent_url="/test/"
    )
    data = {"non_pertinent": True}
    multiform = multiform_class(data)

    assert multiform.forms[0].fields["age"].disabled is True
    assert multiform.forms[0].fields["non_pertinent"].disabled is False


def test_multiform_si_pertinent_validation_sans_non_pertinent(indicateur_si_pertinent):
    multiform_class = create_multiform_from_schema(
        indicateur_si_pertinent, toggle_pertinent_url="/test/"
    )
    data = {"non_pertinent": False}
    multiform = multiform_class(data)

    assert not multiform.is_valid()
    assert (
        "Ce champ est requis lorsque l'indicateur est déclaré comme pertinent"
        in multiform.forms[0].errors["age"]
    )


def test_multiform_si_pertinent_validation_avec_non_pertinent(indicateur_si_pertinent):
    multiform_class = create_multiform_from_schema(
        indicateur_si_pertinent, toggle_pertinent_url="/test/"
    )
    data = {"non_pertinent": True}
    multiform = multiform_class(data)

    assert multiform.is_valid()
    assert multiform.cleaned_data["non_pertinent"] is True
    assert multiform.cleaned_data["age"] is None


def test_multiform_tableau_lignes_fixes_validation(
    indicateur_avec_tableau_lignes_fixes,
):
    multiform_class = create_multiform_from_schema(
        indicateur_avec_tableau_lignes_fixes, toggle_pertinent_url="/test"
    )
    data = {
        "form-TOTAL_FORMS": "3",
        "form-INITIAL_FORMS": "0",
        "form-0-nombre_heures_travaillees": "10",
        "form-0-representation_conseil_administration": True,
        "form-1-nombre_heures_travaillees": "5",
        "form-1-representation_conseil_administration": True,
        "form-2-nombre_heures_travaillees": "2",
        "form-2-representation_conseil_administration": False,
    }
    multiform = multiform_class(data)

    assert multiform.is_valid()
    assert multiform.cleaned_data["repartition"] == {
        "homme": {
            "nombre_heures_travaillees": 10,
            "representation_conseil_administration": True,
        },
        "femme": {
            "nombre_heures_travaillees": 5,
            "representation_conseil_administration": True,
        },
        "autre": {
            "nombre_heures_travaillees": 2,
            "representation_conseil_administration": False,
        },
    }


def test_multiform_tableau_lignes_fixes_suppression_ligne_impossible(
    indicateur_avec_tableau_lignes_fixes,
):
    multiform_class = create_multiform_from_schema(
        indicateur_avec_tableau_lignes_fixes, toggle_pertinent_url="/test"
    )
    data = {
        "form-TOTAL_FORMS": "3",
        "form-INITIAL_FORMS": "0",
        "form-0-nombre_heures_travaillees": "10",
        "form-0-representation_conseil_administration": True,
        "form-1-nombre_heures_travaillees": "5",
        "form-1-representation_conseil_administration": True,
        "form-2-nombre_heures_travaillees": "2",
        "form-2-representation_conseil_administration": False,
        "form-2-DELETE": "on",
    }
    multiform = multiform_class(data)

    assert multiform.is_valid()
    assert multiform.cleaned_data["repartition"]["autre"] == {
        "nombre_heures_travaillees": 2,
        "representation_conseil_administration": False,
    }


def test_multiform_tableau_lignes_fixes_vide_invalide(
    indicateur_avec_tableau_lignes_fixes,
):
    multiform_class = create_multiform_from_schema(
        indicateur_avec_tableau_lignes_fixes, toggle_pertinent_url="/test"
    )
    data = {
        "form-TOTAL_FORMS": "3",
        "form-INITIAL_FORMS": "0",
    }
    multiform = multiform_class(data)

    assert not multiform.is_valid()
