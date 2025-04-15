import pytest
from django.core.management import call_command

import api.exceptions
from entreprises.management.commands.force_categorie_juridique_sirene import (
    Command as CommandCategorieJuridiqueSirene,
)
from entreprises.management.commands.force_code_naf import Command as CommandCodeNAF
from entreprises.management.commands.force_denomination import (
    Command as CommandDenomination,
)
from entreprises.models import CaracteristiquesAnnuelles


@pytest.mark.django_db(transaction=True)
def test_remplit_la_denomination(db, mocker, entreprise_non_qualifiee):
    entreprise_non_qualifiee.denomination = ""
    entreprise_non_qualifiee.save()
    RAISON_SOCIALE = "RAISON SOCIALE"

    mocker.patch(
        "api.recherche_entreprises.recherche_par_siren",
        return_value={
            "siren": entreprise_non_qualifiee.siren,
            "effectif": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
            "denomination": RAISON_SOCIALE,
        },
    )
    CommandDenomination().handle()

    entreprise_non_qualifiee.refresh_from_db()
    assert entreprise_non_qualifiee.denomination == RAISON_SOCIALE


@pytest.mark.django_db(transaction=True)
def test_ne_modifie_pas_la_denomination_si_deja_remplie(
    db, mocker, entreprise_non_qualifiee
):
    RAISON_SOCIALE = entreprise_non_qualifiee.denomination

    mocker.patch(
        "api.recherche_entreprises.recherche_par_siren",
        return_value={
            "siren": entreprise_non_qualifiee.siren,
            "effectif": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
            "denomination": "RAISON SOCIALE",
        },
    )
    CommandDenomination().handle()

    entreprise_non_qualifiee.refresh_from_db()
    assert entreprise_non_qualifiee.denomination == RAISON_SOCIALE


@pytest.mark.django_db(transaction=True)
def test_erreur_de_l_api(capsys, db, mocker, entreprise_non_qualifiee):
    entreprise_non_qualifiee.denomination = ""
    entreprise_non_qualifiee.save()

    mocker.patch(
        "api.recherche_entreprises.recherche_par_siren",
        side_effect=api.exceptions.APIError,
    )
    call_command("force_denomination")

    assert entreprise_non_qualifiee.denomination == ""
    captured = capsys.readouterr()
    assert captured.out.startswith("ERREUR")
    assert captured.out.endswith(f"{entreprise_non_qualifiee.siren}\n")


@pytest.mark.django_db(transaction=True)
def test_remplit_la_categorie_juridique(db, mocker, entreprise_non_qualifiee):
    entreprise_non_qualifiee.denomination = ""
    entreprise_non_qualifiee.categorie_juridique_sirene = None
    entreprise_non_qualifiee.save()
    CATEGORIE_JURIDIQUE_SIRENE = 5555

    mocker.patch(
        "api.recherche_entreprises.recherche_par_siren",
        return_value={
            "siren": entreprise_non_qualifiee.siren,
            "effectif": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
            "denomination": "RAISON_SOCIALE",
            "categorie_juridique_sirene": CATEGORIE_JURIDIQUE_SIRENE,
        },
    )
    CommandCategorieJuridiqueSirene().handle()

    entreprise_non_qualifiee.refresh_from_db()
    assert (
        entreprise_non_qualifiee.categorie_juridique_sirene
        == CATEGORIE_JURIDIQUE_SIRENE
    )


@pytest.mark.django_db(transaction=True)
def test_ne_modifie_pas_la_categorie_juridique_si_deja_remplie(
    db, mocker, entreprise_non_qualifiee
):
    entreprise_non_qualifiee.categorie_juridique_sirene = CATEGORIE_DE_REFERENCE = 4444
    entreprise_non_qualifiee.save()
    CATEGORIE_JURIDIQUE_SIRENE = 5555

    mocker.patch(
        "api.recherche_entreprises.recherche_par_siren",
        return_value={
            "siren": entreprise_non_qualifiee.siren,
            "effectif": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
            "denomination": "RAISON SOCIALE",
            "categorie_juridique_sirene": CATEGORIE_JURIDIQUE_SIRENE,
        },
    )
    CommandCategorieJuridiqueSirene().handle()

    entreprise_non_qualifiee.refresh_from_db()
    assert entreprise_non_qualifiee.categorie_juridique_sirene == CATEGORIE_DE_REFERENCE


@pytest.mark.django_db(transaction=True)
def test_remplit_le_code_NAF(db, mocker, entreprise_non_qualifiee):
    entreprise_non_qualifiee.code_naf = ""
    entreprise_non_qualifiee.save()
    CODE_NAF = "01.11Z"

    mocker.patch(
        "api.recherche_entreprises.recherche_par_siren",
        return_value={
            "siren": entreprise_non_qualifiee.siren,
            "effectif": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
            "denomination": "RAISON_SOCIALE",
            "code_NAF": CODE_NAF,
        },
    )
    CommandCodeNAF().handle()

    entreprise_non_qualifiee.refresh_from_db()
    assert entreprise_non_qualifiee.code_NAF == CODE_NAF


@pytest.mark.django_db(transaction=True)
def test_ne_modifie_pas_le_code_NAF_si_deja_remplie(
    db, mocker, entreprise_non_qualifiee
):
    entreprise_non_qualifiee.code_NAF = CODE_NAF_ENREGISTRE = "20.41Z"
    entreprise_non_qualifiee.save()
    CODE_NAF = "01.11Z"

    mocker.patch(
        "api.recherche_entreprises.recherche_par_siren",
        return_value={
            "siren": entreprise_non_qualifiee.siren,
            "effectif": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
            "denomination": "RAISON SOCIALE",
            "code_NAF": CODE_NAF,
        },
    )
    CommandCodeNAF().handle()

    entreprise_non_qualifiee.refresh_from_db()
    assert entreprise_non_qualifiee.code_NAF == CODE_NAF_ENREGISTRE
