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


def test_nombre_decimal_dans_les_données_non_stockees_d_un_indicateur(rapport_vsme):
    indicateur_nombre_decimal_non_stocké = rapport_vsme.indicateurs.create(
        schema_id="B3-29-p2",
        data={
            "consommation_energie_par_combustible": [
                {"type_combustible": "Biodiesel", "quantite": Decimal("10.4")},
            ],  # type tableau avec une colonne "densite" calculée de type nombre_decimal ajoutée au schema après l'enregistrement de premières données en prod
        },
    )

    indicateur_nombre_decimal_non_stocké.refresh_from_db()
    densité_encodée = indicateur_nombre_decimal_non_stocké._data[
        "consommation_energie_par_combustible"
    ][0].get("densite")
    assert not densité_encodée  # valeur non stockée

    densité_décodée = indicateur_nombre_decimal_non_stocké.data[
        "consommation_energie_par_combustible"
    ][0]["densite"]
    assert isinstance(densité_décodée, Decimal)
    assert densité_décodée == Decimal("0.85")
