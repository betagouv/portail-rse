from datetime import datetime

import pytest
from django.core.exceptions import ValidationError

from reglementations.enums import ENJEUX_NORMALISES
from reglementations.models import DocumentAnalyseIA
from reglementations.models import RapportCSRD

# Fixtures :
# voir pour pull-up éventuel, au besoin


@pytest.fixture
def rapport_personnel(alice, entreprise_non_qualifiee):
    return RapportCSRD.objects.create(
        proprietaire=alice,
        entreprise=entreprise_non_qualifiee,
        annee=f"{datetime.now():%Y}",
    )


@pytest.fixture
def rapport_officiel(alice, entreprise_non_qualifiee):
    # Alice est habilitée à modifier ce rapport officiel
    entreprise_non_qualifiee.users.add(alice)
    return RapportCSRD.objects.create(
        proprietaire=None,
        entreprise=entreprise_non_qualifiee,
        annee=f"{datetime.now():%Y}",
    )


def test_clean_rapport_csrd(rapport_personnel):
    # `clean()` contient quelques vérifications pour voir si un modèle est personnel ou principal
    assert not rapport_personnel.est_officiel()

    # clean doit être sans effet
    rapport_personnel.clean()

    # modification en officiel
    alice = rapport_personnel.proprietaire
    rapport_personnel.proprietaire = None
    rapport_personnel.save()

    assert (
        rapport_personnel.est_officiel
    ), "le rapport CSRD doit être officiel (sans propriétaire)"

    # passage en personnel après avoir été officiel : non
    rapport_personnel.proprietaire = alice
    with pytest.raises(
        ValidationError,
        match="Impossible de modifier le rapport CSRD officiel en rapport personnel",
    ):
        rapport_personnel.clean()

    # enregistrement d'un nouveau rapport officiel : non
    rapport_personnel.pk = None
    rapport_personnel.proprietaire = None
    with pytest.raises(
        ValidationError,
        match="Il existe déjà un rapport CSRD officiel pour cette entreprise",
    ):
        rapport_personnel.clean()


def test_enjeux_normalises_presents(rapport_personnel):
    # les enjeux normalisés doivent être présents sur un nouveau rapport CSRD
    ENJEU_CHANGEMENT_CLIMATIQUE = ENJEUX_NORMALISES[0]
    enjeu = rapport_personnel.enjeux.order_by("id")[0]
    nom, esrs, description = enjeu.nom, enjeu.esrs, enjeu.description
    assert (nom, esrs, description) == (
        ENJEU_CHANGEMENT_CLIMATIQUE.nom,
        ENJEU_CHANGEMENT_CLIMATIQUE.esrs,
        ENJEU_CHANGEMENT_CLIMATIQUE.description,
    )
    assert not enjeu.parent

    ENJEU_RESSOURCES_MARINES = ENJEUX_NORMALISES[10]
    enjeu_ressources_marines = rapport_personnel.enjeux.order_by("id")[10]
    assert not enjeu_ressources_marines.parent

    ENJEU_CONSOMMATION_EAU = ENJEU_RESSOURCES_MARINES.children[0]
    enjeu_consommation_eau = rapport_personnel.enjeux.order_by("id")[11]
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


def test_rapport_personnel_modifiable_par(rapport_personnel, alice, bob):
    # un rapport personnel n'est modifiable que par le propriétaire

    assert rapport_personnel.modifiable_par(
        alice
    ), "Le rapport CSRD doit être modifiable par Alice"
    assert not rapport_personnel.modifiable_par(
        bob
    ), "Le rapport CSRD ne doit pas être modifiable par Bob"


def test_rapport_officiel_modifiable_par(rapport_officiel, alice, bob):
    # un rapport officiel n'est modifiable que par les utilisateurs habilités de l'entreprise

    # on s'assure qu'Alice est bien habilitée
    alice.habilitation_set.update(confirmed_at=datetime.now())

    assert rapport_officiel.modifiable_par(
        alice
    ), "Le rapport CSRD doit être modifiable par Alice"
    assert not rapport_officiel.modifiable_par(
        bob
    ), "Le rapport CSRD ne doit pas être modifiable par Bob"


def test_rapport_csrd_bloque_non_modifiable(rapport_officiel):
    rapport_officiel.description = "Description modifiée"

    rapport_officiel.save()
    rapport_officiel.refresh_from_db()

    assert (
        rapport_officiel.description == "Description modifiée"
    ), "Le rapport CSRD doit être modifiable (non-bloqué)"

    # vérifie que le rapport CSRD n'est plus modifiable après publication du rapport
    rapport_officiel.bloque = True
    rapport_officiel.lien_rapport = "https://exemple.com/rapport"

    initial_description = rapport_officiel.description

    # tente de modifier le rapport sur des champs bloqués
    rapport_officiel.description = "Nouvelle description"
    rapport_officiel.lien_rapport = "https://example.com/nouveau"

    rapport_officiel.save()
    rapport_officiel.refresh_from_db()

    assert (
        rapport_officiel.description == initial_description
    ), "Le rapport CSRD ne devrait pas être modifié (bloqué)"
    assert (
        rapport_officiel.lien_rapport == "https://example.com/nouveau"
    ), "Seul le lien_rapport devrait être modifiable"


def test_rapport_csrd_avec_documents(rapport_personnel):
    document_1 = DocumentAnalyseIA.objects.create(rapport_csrd=rapport_personnel)
    document_2 = DocumentAnalyseIA.objects.create(
        rapport_csrd=rapport_personnel, etat="en attente"
    )

    assert list(rapport_personnel.documents_analyses) == []

    document_2.etat = "success"
    document_2.save()

    assert list(rapport_personnel.documents_analyses) == [document_2]
