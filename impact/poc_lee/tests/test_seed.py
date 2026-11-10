import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError

from entreprises.models import Entreprise
from habilitations.models import Habilitation

MOT_DE_PASSE = "mot-de-passe-de-test"


@pytest.fixture
def mot_de_passe(monkeypatch):
    monkeypatch.setenv("POC_LEE_DEMO_PASSWORD", MOT_DE_PASSE)


def test_cree_les_entreprises_et_l_utilisateur_de_demo(db, mot_de_passe):
    call_command("seed_poc_lee")

    utilisateur = get_user_model().objects.get(email="demo-lee@portail-rse.test")
    entreprises = Entreprise.objects.filter(identifiant__in=["095680393", "045850617"])
    assert sorted(entreprises.values_list("identifiant", flat=True)) == [
        "045850617",
        "095680393",
    ]
    for entreprise in entreprises:
        assert Habilitation.existe(entreprise, utilisateur)
        assert entreprise.dernieres_caracteristiques_qualifiantes is not None
    assert utilisateur.check_password(MOT_DE_PASSE)
    assert not utilisateur.doit_choisir_type_utilisateur


def test_peut_etre_relancee(db, mot_de_passe):
    call_command("seed_poc_lee")
    call_command("seed_poc_lee")

    assert Entreprise.objects.count() == 2
    assert get_user_model().objects.count() == 1


def test_echoue_sans_mot_de_passe(db, monkeypatch):
    monkeypatch.delenv("POC_LEE_DEMO_PASSWORD", raising=False)

    with pytest.raises(CommandError):
        call_command("seed_poc_lee")
