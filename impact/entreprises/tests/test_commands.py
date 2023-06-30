import pytest
from django.core.management import call_command

import api.exceptions
from entreprises.management.commands.force_denomination import Command
from entreprises.models import CaracteristiquesAnnuelles


@pytest.mark.django_db(transaction=True)
def test_remplit_la_denomination(db, mocker, entreprise_non_qualifiee):
    entreprise_non_qualifiee.denomination = ""
    entreprise_non_qualifiee.save()
    RAISON_SOCIALE = "RAISON SOCIALE"

    mocker.patch(
        "api.recherche_entreprises.recherche",
        return_value={
            "siren": entreprise_non_qualifiee.siren,
            "effectif": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
            "denomination": RAISON_SOCIALE,
        },
    )
    Command().handle()

    entreprise_non_qualifiee.refresh_from_db()
    assert entreprise_non_qualifiee.denomination == RAISON_SOCIALE


@pytest.mark.django_db(transaction=True)
def test_ne_modifie_pas_la_denomination_si_deja_remplie(
    db, mocker, entreprise_non_qualifiee
):
    RAISON_SOCIALE = entreprise_non_qualifiee.denomination

    mocker.patch(
        "api.recherche_entreprises.recherche",
        return_value={
            "siren": entreprise_non_qualifiee.siren,
            "effectif": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
            "denomination": "RAISON SOCIALE",
        },
    )
    Command().handle()

    entreprise_non_qualifiee.refresh_from_db()
    assert entreprise_non_qualifiee.denomination == RAISON_SOCIALE


@pytest.mark.django_db(transaction=True)
def test_erreur_de_l_api(capsys, db, mocker, entreprise_non_qualifiee):
    entreprise_non_qualifiee.denomination = ""
    entreprise_non_qualifiee.save()

    mocker.patch(
        "api.recherche_entreprises.recherche", side_effect=api.exceptions.APIError
    )
    call_command("force_denomination")

    assert entreprise_non_qualifiee.denomination == ""
    captured = capsys.readouterr()
    assert captured.out.startswith("ERREUR")
    assert captured.out.endswith(f"{entreprise_non_qualifiee.siren}\n")
