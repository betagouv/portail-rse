from datetime import datetime

import pytest
from django.core.exceptions import ValidationError

from ..models import RapportCSRD
from reglementations.enums import ENJEUX_NORMALISES

# Fixtures :
# voir pour pull-up éventuel, au besoin


@pytest.fixture
def rapport_personnel(alice, entreprise_non_qualifiee):
    return RapportCSRD.objects.create(
        proprietaire=alice,
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