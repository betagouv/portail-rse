import pytest
from django.conf import settings
from django.core.exceptions import ValidationError

from utils.pays import PAYS_DISPONIBLES


def test_pays_disponibles():
    # France, 26 autres pays de l'Union européenne et Maroc
    assert len(PAYS_DISPONIBLES) == 28


@pytest.mark.parametrize(
    "code_pays,saisie,identifiant",
    [
        ("FRA", "552 100 554", "552100554"),
        ("FRA", settings.SIREN_ENTREPRISE_TEST, settings.SIREN_ENTREPRISE_TEST),
        ("DEU", "de 136 695 976", "DE136695976"),
        ("GRC", "EL094259216", "EL094259216"),
        ("MAR", "00 1561 191 000 066", "001561191000066"),
    ],
)
def test_valide_identifiant_renvoie_la_forme_compacte(code_pays, saisie, identifiant):
    assert PAYS_DISPONIBLES[code_pays].valide_identifiant(saisie) == identifiant


@pytest.mark.parametrize(
    "code_pays,identifiant,erreur",
    [
        ("FRA", "123456789", "Le siren est incorrect"),
        ("DEU", "DE136695978", "Le numéro de TVA intracommunautaire est invalide."),
        ("AUT", "DE136695976", "Le numéro de TVA intracommunautaire doit commencer par AT."),
        ("MAR", "001561191000065", "Le numéro ICE est invalide."),
    ],
)
def test_valide_identifiant_leve_une_erreur(code_pays, identifiant, erreur):
    with pytest.raises(ValidationError) as exc_info:
        PAYS_DISPONIBLES[code_pays].valide_identifiant(identifiant)

    assert exc_info.value.messages == [erreur]
