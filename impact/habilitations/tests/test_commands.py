import pytest
from django.conf import settings

from habilitations.management.commands.supprime_utilisateurs_sur_entreprise_test import (
    Command,
)
from habilitations.models import Habilitation
from users.models import User


@pytest.mark.django_db(transaction=True)
def test_nettoie_entreprise_test_supprime_ses_utilisateurs_sauf_le_contact(
    db, mocker, entreprise_factory, alice, bob
):
    entreprise = entreprise_factory(siren="000000001")
    Habilitation.ajouter(entreprise, alice)
    Habilitation.ajouter(entreprise, bob)
    contact = User.objects.create(email=settings.SUPPORT_EMAIL)
    Habilitation.ajouter(entreprise, contact)
    autre_entreprise = entreprise_factory(siren="123456789")
    Habilitation.ajouter(autre_entreprise, alice)
    Habilitation.ajouter(autre_entreprise, bob)

    Command().handle()

    entreprise.refresh_from_db()
    assert entreprise.habilitation_set.count() == 1  # uniquement contact
    autre_entreprise.refresh_from_db()
    assert autre_entreprise.habilitation_set.count() == 2  # alice et bob


@pytest.mark.django_db(transaction=True)
def test_nettoie_entreprise_test_ne_supprime_pas_adresse_de_contact(
    db, mocker, entreprise_factory
):
    entreprise = entreprise_factory(siren="000000001")
    contact = User.objects.create(email=settings.SUPPORT_EMAIL)
    Habilitation.ajouter(entreprise, contact)

    Command().handle()

    entreprise.refresh_from_db()
    assert entreprise.habilitation_set.count() == 1


@pytest.mark.django_db(transaction=True)
def test_nettoie_entreprise_test_sans_action_si_pas_d_entreprise_test(db, mocker):
    valeur_retour = Command().handle()

    assert valeur_retour == None
