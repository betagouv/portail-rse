from unittest.mock import Mock

import pytest

from habilitations.context_processors import habilitation
from habilitations.enums import UserRole
from habilitations.models import Habilitation


@pytest.mark.django_db
def test_habilitation_sans_requete_supplementaire(
    alice, entreprise_factory, django_assert_num_queries
):
    entreprise_1 = entreprise_factory(siren="000000001")
    entreprise_2 = entreprise_factory(siren="000000002")
    Habilitation.ajouter(entreprise_1, alice, role=UserRole.ADMINISTRATEUR)
    Habilitation.ajouter(entreprise_2, alice, role=UserRole.LECTEUR)

    request = Mock()
    request.session = {"entreprise": entreprise_2.id}
    request.habilitations = list(alice.habilitation_set.all())

    with django_assert_num_queries(0):
        ctx = habilitation(request)

    assert ctx["role_utilisateur"] == UserRole.LECTEUR
    assert ctx["est_lecteur"]
    assert not ctx["est_contributeur"]
    assert not ctx["est_administrateur"]


def test_habilitation_sans_entreprise_en_session():
    request = Mock()
    request.session = {}

    assert habilitation(request) == {}
