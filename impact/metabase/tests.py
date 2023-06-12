import pytest

from entreprises.models import Evolution
from impact.settings import METABASE_DATABASE_NAME
from metabase.management.commands.sync_metabase import Command
from metabase.models import Entreprise as MetabaseEntreprise


@pytest.mark.django_db(transaction=True, databases=["default", METABASE_DATABASE_NAME])
def test_synchronise_metabase_once(entreprise_factory):
    entreprise_A = entreprise_factory(
        siren="000000001",
        denomination="A",
        effectif=Evolution.EFFECTIF_ENTRE_300_ET_499,
        bdese_accord=True,
    )

    Command().handle()

    metabase_entreprise = MetabaseEntreprise.objects.all()[0]
    assert metabase_entreprise.denomination == "A"
    assert metabase_entreprise.siren == "000000001"
    assert metabase_entreprise.effectif == "300-499"
    assert metabase_entreprise.bdese_accord == True
    assert metabase_entreprise.created_at == entreprise_A.created_at
    assert metabase_entreprise.updated_at == entreprise_A.updated_at


@pytest.mark.django_db(transaction=True, databases=["default", METABASE_DATABASE_NAME])
def test_synchronise_several_times(entreprise_factory):
    entreprise_A = entreprise_factory(
        siren="000000001",
        denomination="A",
        effectif=Evolution.EFFECTIF_MOINS_DE_50,
        bdese_accord=True,
    )

    Command().handle()
    Command().handle()

    metabase_entreprise = MetabaseEntreprise.objects.all()[0]
    assert metabase_entreprise.denomination == "A"
    assert metabase_entreprise.siren == "000000001"
    assert metabase_entreprise.effectif == "0-49"
    assert metabase_entreprise.bdese_accord == True
