from analyseia.models import AnalyseIA


def test_liee_a_une_entreprise(entreprise_factory):
    entreprise = entreprise_factory()

    document = AnalyseIA.objects.create()
    entreprise.analyses_ia.add(document)

    assert document.est_liee_a_une_entreprise


def test_liee_a_une_csrd(csrd):
    document = AnalyseIA.objects.create()

    document.rapports_csrd.add(csrd)

    assert not document.est_liee_a_une_entreprise


ANALYSES_V2 = [
    AnalyseIA(
        etat_v2="success",
        resultat_json_v2={
            "B3-30-p1": [
                {
                    "unite": "tonne",
                    "valeur": "12",
                    "paragraphe": "Emission de 12 tonnes environ",
                    "champ_id": "estimation_emissions_GES",
                    "colonne_id": "scope_1",
                },
            ]
        },
    ),
]


def test_stats_v2():
    analyse = AnalyseIA(
        etat_v2="success",
        resultat_json_v2={
            "B2-26-p2": [
                {
                    "unite": "euros",
                    "valeur": "9876",
                    "paragraphe": "Investissement de 9876 euros dans l'ESS",
                    "champ_id": "investissement_economie_sociale",
                    "colonne_id": None,
                }
            ],
            "B3-30-p1": [
                {
                    "unite": "tonne",
                    "valeur": "12",
                    "paragraphe": "Emission de 12 tonnes environ",
                    "champ_id": "estimation_emissions_GES",
                    "colonne_id": "scope_1",
                },
                {
                    "unite": None,
                    "valeur": "1234",
                    "paragraphe": "PARAGRAPHE",
                    "champ_id": "estimation_emissions_GES",
                    "colonne_id": None,
                },
            ],
        },
    )

    assert analyse.nombre_d_indicateurs == 2
    assert analyse.nombre_d_informations == 3
