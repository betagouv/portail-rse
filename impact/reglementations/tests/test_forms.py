from entreprises.models import CaracteristiquesAnnuelles
from entreprises.models import DENOMINATION_MAX_LENGTH
from reglementations.forms import SimulationForm


def test_ignore_bilan_et_ca_consolides_lorsque_pas_de_comptes_consolides():
    data = {
        "siren": "123456789",
        "denomination": "Entreprise SAS",
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_ENTRE_700K_ET_12M,
        "tranche_bilan": CaracteristiquesAnnuelles.BILAN_ENTRE_6M_ET_20M,
        "appartient_groupe": True,
        "comptes_consolides": False,
        "tranche_chiffre_affaires_consolide": CaracteristiquesAnnuelles.CA_ENTRE_700K_ET_12M,
        "tranche_bilan_consolide": CaracteristiquesAnnuelles.BILAN_ENTRE_6M_ET_20M,
    }

    form = SimulationForm(data=data)

    assert form.is_valid(), form.errors
    assert form.cleaned_data["tranche_chiffre_affaires_consolide"] is None
    assert form.cleaned_data["tranche_bilan_consolide"] is None


def test_pas_de_comptes_consolides_si_pas_de_groupe():
    data = {
        "siren": "123456789",
        "denomination": "Entreprise SAS",
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_ENTRE_700K_ET_12M,
        "tranche_bilan": CaracteristiquesAnnuelles.BILAN_ENTRE_6M_ET_20M,
        "appartient_groupe": False,
        "comptes_consolides": True,
        "tranche_chiffre_affaires_consolide": CaracteristiquesAnnuelles.CA_ENTRE_700K_ET_12M,
        "tranche_bilan_consolide": CaracteristiquesAnnuelles.BILAN_ENTRE_6M_ET_20M,
    }

    form = SimulationForm(data=data)

    assert form.is_valid(), form.errors
    assert form.cleaned_data["comptes_consolides"] == False
    assert form.cleaned_data["tranche_chiffre_affaires_consolide"] is None
    assert form.cleaned_data["tranche_bilan_consolide"] is None


def test_tronque_la_raison_sociale_si_trop_longue():
    data = {
        "siren": "123456789",
        "denomination": "a" * (DENOMINATION_MAX_LENGTH + 1),
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_ENTRE_700K_ET_12M,
        "tranche_bilan": CaracteristiquesAnnuelles.BILAN_ENTRE_6M_ET_20M,
        "appartient_groupe": True,
        "comptes_consolides": False,
        "tranche_chiffre_affaires_consolide": CaracteristiquesAnnuelles.CA_ENTRE_700K_ET_12M,
        "tranche_bilan_consolide": CaracteristiquesAnnuelles.BILAN_ENTRE_6M_ET_20M,
    }

    form = SimulationForm(data=data)

    assert form.is_valid(), form.errors
    assert form.cleaned_data["denomination"] == "a" * DENOMINATION_MAX_LENGTH
