import pytest

from habilitations.management.commands.supprime_utilisateurs_sur_entreprise_test import (
    Command,
)
from habilitations.models import Habilitation


@pytest.mark.django_db(transaction=True)
def test_nettoie_entreprise_test_supprime_ses_utilisateurs(
    db, mocker, entreprise_factory, alice, bob
):
    entreprise = entreprise_factory(siren="000000001")
    Habilitation.ajouter(entreprise, alice)
    Habilitation.ajouter(entreprise, bob)
    autre_entreprise = entreprise_factory(siren="123456789")
    Habilitation.ajouter(autre_entreprise, alice)
    Habilitation.ajouter(autre_entreprise, bob)

    Command().handle()

    entreprise.refresh_from_db()
    assert entreprise.habilitation_set.count() == 0
    autre_entreprise.refresh_from_db()
    assert autre_entreprise.habilitation_set.count() == 2


@pytest.mark.django_db(transaction=True)
def test_nettoie_entreprise_test_sans_action_si_pas_d_entreprise_test(db, mocker):
    valeur_retour = Command().handle()

    assert valeur_retour == None
