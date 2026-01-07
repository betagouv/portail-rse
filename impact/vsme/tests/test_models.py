from decimal import Decimal


def test_nombre_decimal_dans_les_donnees_d_un_indicateur(rapport_vsme):
    indicateur_simple = rapport_vsme.indicateurs.create(
        schema_id="B1-24-e-v",
        data={
            "methode_comptabilisation": "ETP",
            "nombre_salaries": Decimal("42.5"),  # type nombre_decimal
        },
    )

    indicateur_simple.refresh_from_db()
    nb_salaries_encodé = indicateur_simple._data["nombre_salaries"]
    assert isinstance(nb_salaries_encodé, str)
    assert nb_salaries_encodé == "42.5"

    nb_salaries_décodé = indicateur_simple.data["nombre_salaries"]
    assert isinstance(nb_salaries_décodé, Decimal)
    assert nb_salaries_décodé == Decimal("42.5")

    indicateur_tableau = rapport_vsme.indicateurs.create(
        schema_id="B4-32-p1",
        data={
            "non_pertinent": False,
            "pollution_air": [
                {"polluant": "Anthracène", "unite": "kilos", "valeur": Decimal("11.0")},
            ],  # type tableau avec une colonne "valeur" de type nombre_decimal
        },
    )

    indicateur_tableau.refresh_from_db()
    valeur_encodée = indicateur_tableau._data["pollution_air"][0]["valeur"]
    assert isinstance(valeur_encodée, str)
    assert valeur_encodée == "11.0"

    valeur_décodée = indicateur_tableau.data["pollution_air"][0]["valeur"]
    assert isinstance(valeur_décodée, Decimal)
    assert valeur_décodée == Decimal("11.0")

    indicateur_tableau_lignes_fixes = rapport_vsme.indicateurs.create(
        schema_id="B8-39-a",
        data={
            "effectifs_type_de_contrat": {
                "contrat_permanent": {"nombre_salaries": Decimal("40.5")},
                "contrat_temporaire": {"nombre_salaries": Decimal("1.5")},
            },  # type tableau_lignes_fixes avec une colonne "nombre_salaries" de type nombre_decimal
        },
    )

    indicateur_tableau_lignes_fixes.refresh_from_db()
    nb_salaries_encodé = indicateur_tableau_lignes_fixes._data[
        "effectifs_type_de_contrat"
    ]["contrat_permanent"]["nombre_salaries"]
    assert isinstance(nb_salaries_encodé, str)
    assert nb_salaries_encodé == "40.5"

    nb_salaries_décodé = indicateur_tableau_lignes_fixes.data[
        "effectifs_type_de_contrat"
    ]["contrat_permanent"]["nombre_salaries"]
    assert isinstance(nb_salaries_décodé, Decimal)
    assert nb_salaries_décodé == Decimal("40.5")
