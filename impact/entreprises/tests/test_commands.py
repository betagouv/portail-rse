import pytest
from django.core.management import call_command

import api.exceptions
from entreprises.management.commands.force_raison_sociale import Command
from entreprises.models import Entreprise as Entreprise


@pytest.mark.django_db(transaction=True)
def test_remplit_la_raison_sociale(db, mocker, unqualified_entreprise):
    unqualified_entreprise.raison_sociale = ""
    unqualified_entreprise.save()
    RAISON_SOCIALE = "RAISON SOCIALE"

    mocker.patch(
        "api.recherche_entreprises.recherche",
        return_value={
            "siren": unqualified_entreprise.siren,
            "effectif": "moyen",
            "raison_sociale": RAISON_SOCIALE,
        },
    )
    Command().handle()

    unqualified_entreprise.refresh_from_db()
    assert unqualified_entreprise.raison_sociale == RAISON_SOCIALE


@pytest.mark.django_db(transaction=True)
def test_ne_modifie_pas_la_raison_sociale_si_deja_remplie(
    db, mocker, unqualified_entreprise
):
    RAISON_SOCIALE = unqualified_entreprise.raison_sociale

    mocker.patch(
        "api.recherche_entreprises.recherche",
        return_value={
            "siren": unqualified_entreprise.siren,
            "effectif": "moyen",
            "raison_sociale": "RAISON SOCIALE",
        },
    )
    Command().handle()

    unqualified_entreprise.refresh_from_db()
    assert unqualified_entreprise.raison_sociale == RAISON_SOCIALE


@pytest.mark.django_db(transaction=True)
def test_erreur_de_l_api(capsys, db, mocker, unqualified_entreprise):
    unqualified_entreprise.raison_sociale = ""
    unqualified_entreprise.save()

    mocker.patch(
        "api.recherche_entreprises.recherche", side_effect=api.exceptions.APIError
    )
    call_command("force_raison_sociale")

    assert unqualified_entreprise.raison_sociale == ""
    captured = capsys.readouterr()
    assert captured.out.startswith("ERREUR")
    assert captured.out.endswith(f"{unqualified_entreprise.siren}\n")
