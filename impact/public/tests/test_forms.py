from conftest import CODE_PAYS_PORTUGAL
from entreprises.models import CaracteristiquesAnnuelles
from entreprises.models import DENOMINATION_MAX_LENGTH
from public.forms import SimulationForm


def test_ignore_bilan_et_ca_consolides_lorsque_pas_de_comptes_consolides():
    data = {
        "siren": "123456789",
        "denomination": "Entreprise SAS",
        "categorie_juridique_sirene": 5710,
        "code_pays_etranger_sirene": CODE_PAYS_PORTUGAL,
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_ENTRE_700K_ET_12M,
        "tranche_bilan": CaracteristiquesAnnuelles.BILAN_ENTRE_6M_ET_20M,
        "appartient_groupe": True,
        "effectif_groupe": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "societe_mere_en_france": True,
        "comptes_consolides": False,
        "tranche_chiffre_affaires_consolide": CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
        "tranche_bilan_consolide": CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
    }

    form = SimulationForm(data=data)

    assert form.is_valid(), form.errors
    assert form.cleaned_data["tranche_chiffre_affaires_consolide"] is None
    assert form.cleaned_data["tranche_bilan_consolide"] is None


def test_ignore_effectif_groupe_societe_mere_et_comptes_consolides_lorsque_pas_de_groupe():
    data = {
        "siren": "123456789",
        "denomination": "Entreprise SAS",
        "categorie_juridique_sirene": 5710,
        "code_pays_etranger_sirene": CODE_PAYS_PORTUGAL,
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_ENTRE_700K_ET_12M,
        "tranche_bilan": CaracteristiquesAnnuelles.BILAN_ENTRE_6M_ET_20M,
        "appartient_groupe": False,
        "est_societe_mere": True,
        "effectif_groupe": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "comptes_consolides": True,
        "tranche_chiffre_affaires_consolide": CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
        "tranche_bilan_consolide": CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
    }

    form = SimulationForm(data=data)

    assert form.is_valid(), form.errors
    assert form.cleaned_data["est_societe_mere"] is None
    assert form.cleaned_data["effectif_groupe"] is None
    assert form.cleaned_data["comptes_consolides"] is None
    assert form.cleaned_data["tranche_chiffre_affaires_consolide"] is None
    assert form.cleaned_data["tranche_bilan_consolide"] is None


def test_tronque_la_raison_sociale_si_trop_longue():
    data = {
        "siren": "123456789",
        "denomination": "a" * (DENOMINATION_MAX_LENGTH + 1),
        "categorie_juridique_sirene": 5710,
        "code_pays_etranger_sirene": CODE_PAYS_PORTUGAL,
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_ENTRE_700K_ET_12M,
        "tranche_bilan": CaracteristiquesAnnuelles.BILAN_ENTRE_6M_ET_20M,
        "appartient_groupe": True,
        "effectif_groupe": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "comptes_consolides": False,
        "tranche_chiffre_affaires_consolide": "",
        "tranche_bilan_consolide": "",
    }

    form = SimulationForm(data=data)

    assert form.is_valid(), form.errors
    assert form.cleaned_data["denomination"] == "a" * DENOMINATION_MAX_LENGTH


def test_erreur_si_appartient_groupe_sans_effectif_groupe():
    data = {
        "siren": "123456789",
        "denomination": "Entreprise SAS",
        "categorie_juridique_sirene": 5710,
        "code_pays_etranger_sirene": CODE_PAYS_PORTUGAL,
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_ENTRE_700K_ET_12M,
        "tranche_bilan": CaracteristiquesAnnuelles.BILAN_ENTRE_6M_ET_20M,
        "appartient_groupe": True,
        "effectif_groupe": "",
        "comptes_consolides": False,
        "tranche_chiffre_affaires_consolide": "",
        "tranche_bilan_consolide": "",
    }

    form = SimulationForm(data=data)

    assert not form.is_valid()
    assert (
        form.errors["effectif_groupe"][0]
        == "Ce champ est obligatoire lorsque l'entreprise appartient à un groupe"
    )


def test_erreur_si_comptes_consolides_sans_bilan_consolide():
    data = {
        "siren": "123456789",
        "denomination": "Entreprise SAS",
        "categorie_juridique_sirene": 5710,
        "code_pays_etranger_sirene": CODE_PAYS_PORTUGAL,
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_ENTRE_700K_ET_12M,
        "tranche_bilan": CaracteristiquesAnnuelles.BILAN_ENTRE_6M_ET_20M,
        "appartient_groupe": True,
        "effectif_groupe": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "comptes_consolides": True,
        "tranche_chiffre_affaires_consolide": CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
        "tranche_bilan_consolide": "",
    }
    form = SimulationForm(data=data)

    assert not form.is_valid()
    assert (
        form.errors["tranche_bilan_consolide"][0]
        == "Ce champ est obligatoire lorsque les comptes sont consolidés"
    )


def test_erreur_si_comptes_consolides_sans_ca_consolide():
    data = {
        "siren": "123456789",
        "denomination": "Entreprise SAS",
        "categorie_juridique_sirene": 5710,
        "code_pays_etranger_sirene": CODE_PAYS_PORTUGAL,
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_ENTRE_700K_ET_12M,
        "tranche_bilan": CaracteristiquesAnnuelles.BILAN_ENTRE_6M_ET_20M,
        "appartient_groupe": True,
        "effectif_groupe": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "comptes_consolides": True,
        "tranche_chiffre_affaires_consolide": "",
        "tranche_bilan_consolide": CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
    }

    form = SimulationForm(data=data)

    assert not form.is_valid()
    assert (
        form.errors["tranche_chiffre_affaires_consolide"][0]
        == "Ce champ est obligatoire lorsque les comptes sont consolidés"
    )
