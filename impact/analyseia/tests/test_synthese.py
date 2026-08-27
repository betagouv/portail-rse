from analyseia.helpers import synthese_analyse_v1
from analyseia.helpers import synthese_analyse_v2
from analyseia.models import AnalyseIA

ANALYSES = [
    AnalyseIA(
        etat_v1="success",
        resultat_json_v1="""{
  "ESRS E1": [
    {
      "PAGES": 1,
      "TEXTS": "A"
    },
    {
      "PAGES": 1,
      "TEXTS": "B"
    }
  ],
  "Non ESRS": [
    {
      "PAGES": 4,
      "TEXTS": "C"
    }
  ]
  }""",
    ),
    AnalyseIA(
        etat_v1="success",
        resultat_json_v1="""{
  "ESRS E2 - Pollution": [
    {
      "PAGES": 6,
      "TEXTS": "D"
    }
  ],
  "ESRS S3 : Communautés affectées": [
    {
      "PAGES": 7,
      "TEXTS": "E"
    }
  ],
  "Non ESRS": [
    {
      "PAGES": 8,
      "TEXTS": "F"
    }
  ]
  }""",
    ),
]


def test_synthese_analyse_avec_prefixe_ESRS():
    stats = synthese_analyse_v1(ANALYSES, prefixe_ESRS=True)

    assert stats == {
        "phrases_environnement": [
            {
                "nombre_phrases": 2,
                "titre": "ESRS E1 - Changement climatique",
                "code_esrs": "E1",
            },
            {
                "nombre_phrases": 1,
                "titre": "ESRS E2 - Pollution",
                "code_esrs": "E2",
            },
        ],
        "phrases_social": [
            {
                "nombre_phrases": 1,
                "titre": "ESRS S3 - Communautés affectées",
                "code_esrs": "S3",
            },
        ],
        "phrases_gouvernance": [],
        "nb_phrases_pertinentes_detectees": 4,
        "nb_documents_analyses": 2,
        "nb_esrs_thematiques_detectees": 3,
    }


def test_synthese_analyse_sans_prefixe_ESRS():
    stats = synthese_analyse_v1(ANALYSES, prefixe_ESRS=False)

    assert stats == {
        "phrases_environnement": [
            {
                "nombre_phrases": 2,
                "titre": "Changement climatique",
                "code_esrs": "E1",
            },
            {
                "nombre_phrases": 1,
                "titre": "Pollution",
                "code_esrs": "E2",
            },
        ],
        "phrases_social": [
            {
                "nombre_phrases": 1,
                "titre": "Communautés affectées",
                "code_esrs": "S3",
            },
        ],
        "phrases_gouvernance": [],
        "nb_phrases_pertinentes_detectees": 4,
        "nb_documents_analyses": 2,
        "nb_esrs_thematiques_detectees": 3,
    }


ANALYSES_V2 = [
    AnalyseIA(
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
    ),
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


def test_synthese_analyse_v2():
    stats = synthese_analyse_v2(ANALYSES_V2)

    assert stats == {
        "nb_phrases_pertinentes_detectees": 4,
        "nb_documents_analyses": 2,
        "nb_champs_differents_detectes": 3,
    }
