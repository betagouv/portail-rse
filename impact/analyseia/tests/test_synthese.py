from analyseia.helpers import synthese_analyse
from analyseia.models import AnalyseIA

ANALYSES = [
    AnalyseIA(
        etat="success",
        resultat_json="""{
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
        etat="success",
        resultat_json="""{
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
    stats = synthese_analyse(ANALYSES, prefixe_ESRS=True)

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
    stats = synthese_analyse(ANALYSES, prefixe_ESRS=False)

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
