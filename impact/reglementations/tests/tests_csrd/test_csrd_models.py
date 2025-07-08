import pytest
from django.core.exceptions import ValidationError

from reglementations.enums import ENJEUX_NORMALISES
from reglementations.models import DocumentAnalyseIA
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


def test_rapport_csrd_avec_documents(csrd):
    document_1 = DocumentAnalyseIA.objects.create(rapport_csrd=csrd)
    document_2 = DocumentAnalyseIA.objects.create(rapport_csrd=csrd, etat="pending")

    assert list(csrd.documents_analyses) == []
    assert list(csrd.documents_non_analyses) == [document_1]
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

    assert list(csrd.documents_analyses) == [document_2]
    assert document_2.nombre_de_phrases_pertinentes == 3
