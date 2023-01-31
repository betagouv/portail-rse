import pytest

from django.urls import reverse
from entreprises.models import Entreprise as ImpactEntreprise
from metabase.models import Entreprise as MetabaseEntreprise
from metabase.management.commands.sync_db import Command


@pytest.mark.django_db(transaction=True, databases=["default", "metabase"])
def test_sync_db():
    ImpactEntreprise.objects.create(
        siren="000000001",
        effectif="petit",
        bdese_accord=True,
        raison_sociale="A",
    )

    Command().handle()

    metabase_entreprise = MetabaseEntreprise.objects.all()[0]
    assert metabase_entreprise.raison_sociale == "A"
    assert metabase_entreprise.siren == "000000001"
    assert metabase_entreprise.effectif == "petit"
    assert metabase_entreprise.bdese_accord == True
