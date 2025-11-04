import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse_lazy

from analyseia.models import AnalyseIA
from reglementations.enums import ENJEUX_NORMALISES
from reglementations.enums import EtapeCSRD
from reglementations.enums import ETAPES_CSRD
from reglementations.models import RapportCSRD


def test_impossible_de_creer_plusieurs_rapports_pour_les_mêmes_entreprise_et_annee(
    entreprise_factory, alice
):
    entreprise = entreprise_factory()
    RapportCSRD.objects.create(
        entreprise=entreprise,
        annee=2024,
    )

    with pytest.raises(ValidationError):
        RapportCSRD.objects.create(
            entreprise=entreprise,
            annee=2024,
        )


def test_possible_de_creer_plusieurs_rapports_officiels_pour_des_annees_differentes(
    entreprise_factory,
):
    entreprise = entreprise_factory()
    RapportCSRD.objects.create(
        entreprise=entreprise,
        annee=2024,
    )
    RapportCSRD.objects.create(
        entreprise=entreprise,
        annee=2025,
    )


def test_enjeux_normalises_presents(csrd):
    # les enjeux normalisés doivent être présents sur un nouveau rapport CSRD
    ENJEU_CHANGEMENT_CLIMATIQUE = ENJEUX_NORMALISES[0]
    enjeu = csrd.enjeux.order_by("id")[0]
    nom, esrs, description = enjeu.nom, enjeu.esrs, enjeu.description
    assert (nom, esrs, description) == (
        ENJEU_CHANGEMENT_CLIMATIQUE.nom,
        ENJEU_CHANGEMENT_CLIMATIQUE.esrs,
        ENJEU_CHANGEMENT_CLIMATIQUE.description,
    )
    assert not enjeu.parent

    ENJEU_RESSOURCES_MARINES = ENJEUX_NORMALISES[10]
    enjeu_ressources_marines = csrd.enjeux.order_by("id")[10]
    assert not enjeu_ressources_marines.parent

    ENJEU_CONSOMMATION_EAU = ENJEU_RESSOURCES_MARINES.children[0]
    enjeu_consommation_eau = csrd.enjeux.order_by("id")[11]
    nom, esrs, description = (
        enjeu_consommation_eau.nom,
        enjeu_consommation_eau.esrs,
        enjeu_consommation_eau.description,
    )
    assert (nom, esrs, description) == (
        ENJEU_CONSOMMATION_EAU.nom,
        ENJEU_CONSOMMATION_EAU.esrs,
        ENJEU_CONSOMMATION_EAU.description,
    )
    assert enjeu_consommation_eau.parent == enjeu_ressources_marines


def test_rapport_csrd_bloque_non_modifiable(csrd):
    csrd.description = "Description modifiée"

    csrd.save()
    csrd.refresh_from_db()

    assert (
        csrd.description == "Description modifiée"
    ), "Le rapport CSRD doit être modifiable (non-bloqué)"

    # vérifie que le rapport CSRD n'est plus modifiable après publication du rapport
    csrd.bloque = True
    csrd.lien_rapport = "https://exemple.com/rapport"

    initial_description = csrd.description

    # tente de modifier le rapport sur des champs bloqués
    csrd.description = "Nouvelle description"
    csrd.lien_rapport = "https://example.com/nouveau"

    csrd.save()
    csrd.refresh_from_db()

    assert (
        csrd.description == initial_description
    ), "Le rapport CSRD ne devrait pas être modifié (bloqué)"
    assert (
        csrd.lien_rapport == "https://example.com/nouveau"
    ), "Seul le lien_rapport devrait être modifiable"


def test_debut_avancement_etapes_csrd(csrd):
    assert not csrd.etape_validee
    assert len(csrd.avancement_etapes()) == 3

    id_sous_etape_selection_enjeux = EtapeCSRD.ETAPES_VALIDABLES[1]
    id_sous_etape_analyse_materialite = EtapeCSRD.ETAPES_VALIDABLES[2]
    id_sous_etape_selection_informations = EtapeCSRD.ETAPES_VALIDABLES[3]

    # par défaut, rien n'est validé
    for index, action in enumerate(csrd.avancement_etapes(), start=1):
        assert action["etape"] == ETAPES_CSRD[index]
        assert action["validee"] == False
    assert csrd.avancement_etapes()[0]["lien"] == reverse_lazy(
        "reglementations:gestion_csrd",
        kwargs={
            "siren": csrd.entreprise.siren,
            "id_etape": id_sous_etape_selection_enjeux,
        },
    )

    # rien n'est validé car seule la première sous-etape est validée
    csrd.etape_validee = id_sous_etape_selection_enjeux
    for action in csrd.avancement_etapes():
        assert action["validee"] == False
    assert csrd.avancement_etapes()[0]["lien"] == reverse_lazy(
        "reglementations:gestion_csrd",
        kwargs={
            "siren": csrd.entreprise.siren,
            "id_etape": id_sous_etape_selection_enjeux,
        },
    )

    # la première étape est validée car la seconde sous-etape est validée
    # on considère donc que la première sous-étape l'est aussi
    csrd.etape_validee = id_sous_etape_analyse_materialite
    assert csrd.avancement_etapes()[0] == {
        "etape": ETAPES_CSRD[1],
        "validee": True,
        "lien": reverse_lazy(
            "reglementations:gestion_csrd",
            kwargs={
                "siren": csrd.entreprise.siren,
                "id_etape": id_sous_etape_analyse_materialite,
            },
        ),
    }
    # et pour la seconde étape, on ira sur la première sous-étape
    assert csrd.avancement_etapes()[1] == {
        "etape": ETAPES_CSRD[2],
        "validee": False,
        "lien": reverse_lazy(
            "reglementations:gestion_csrd",
            kwargs={
                "siren": csrd.entreprise.siren,
                "id_etape": id_sous_etape_selection_informations,
            },
        ),
    }

    # la première étape est validée car la première sous-etape
    # de la seconde étape est validée
    csrd.etape_validee = id_sous_etape_selection_informations
    assert csrd.avancement_etapes()[0] == {
        "etape": ETAPES_CSRD[1],
        "validee": True,
        "lien": reverse_lazy(
            "reglementations:gestion_csrd",
            kwargs={
                "siren": csrd.entreprise.siren,
                "id_etape": id_sous_etape_analyse_materialite,
            },
        ),
    }
    for action in csrd.avancement_etapes()[1:]:
        assert action["validee"] == False

    # la première étape est validée car la première sous-etape
    # de la seconde étape est validée
    csrd.etape_validee = id_sous_etape_selection_informations
    assert csrd.avancement_etapes()[0] == {
        "etape": ETAPES_CSRD[1],
        "validee": True,
        "lien": reverse_lazy(
            "reglementations:gestion_csrd",
            kwargs={
                "siren": csrd.entreprise.siren,
                "id_etape": id_sous_etape_analyse_materialite,
            },
        ),
    }
    for action in csrd.avancement_etapes()[1:]:
        assert action["validee"] == False


def test_fin_avancement_etapes_csrd(csrd):
    id_etape_redaction = EtapeCSRD.ETAPES_VALIDABLES[-1]

    # dernière étape validée
    csrd.lien_rapport = "https://csrd.example"

    # tout est validé
    for index, action in enumerate(csrd.avancement_etapes(), start=1):
        assert action["etape"] == ETAPES_CSRD[index]
        assert action["validee"] == True
    assert csrd.avancement_etapes()[-1]["lien"] == reverse_lazy(
        "reglementations:gestion_csrd",
        kwargs={
            "siren": csrd.entreprise.siren,
            "id_etape": id_etape_redaction,
        },
    )


def test_progression_avancement_csrd(csrd):
    id_sous_etape_selection_enjeux = EtapeCSRD.ETAPES_VALIDABLES[1]
    id_sous_etape_analyse_materialite = EtapeCSRD.ETAPES_VALIDABLES[2]
    id_sous_etape_selection_informations = EtapeCSRD.ETAPES_VALIDABLES[3]

    assert csrd.progression() == {"max": 5, "actuel": 0, "pourcent": 0}

    csrd.etape_validee = id_sous_etape_selection_enjeux
    assert csrd.progression() == {"max": 5, "actuel": 1, "pourcent": 20}

    csrd.etape_validee = id_sous_etape_analyse_materialite
    assert csrd.progression() == {"max": 5, "actuel": 2, "pourcent": 40}

    csrd.etape_validee = id_sous_etape_selection_informations
    assert csrd.progression() == {"max": 5, "actuel": 3, "pourcent": 60}

    csrd.lien_rapport = "https://csrd.example"
    assert csrd.progression() == {"max": 5, "actuel": 5, "pourcent": 100}


def test_rapport_csrd_avec_documents(csrd):
    document_1 = AnalyseIA.objects.create()
    document_1.rapports_csrd.add(csrd)
    document_2 = AnalyseIA.objects.create(etat="pending")
    document_2.rapports_csrd.add(csrd)

    assert list(csrd.analyses_ia.reussies()) == []
    assert list(csrd.analyses_ia.non_lancees()) == [document_1]
    assert document_1.nombre_de_phrases_pertinentes == 0
    assert document_2.nombre_de_phrases_pertinentes == 0

    document_2.etat = "success"
    document_2.resultat_json = """{
    "ESRS E1": [
      {
        "PAGES": 1,
        "TEXTS": "A"
      },
      {
        "PAGES": 2,
        "TEXTS": "B"
      }
    ],
    "ESRS E2": [
      {
        "PAGES": 4,
        "TEXTS": "C"
      }
    ],
    "Non ESRS": [
      {
        "PAGES": 22,
        "TEXTS": "X"
      }
    ]
    }"""
    document_2.save()

    assert list(csrd.analyses_ia.reussies()) == [document_2]
    assert document_2.nombre_de_phrases_pertinentes == 3
