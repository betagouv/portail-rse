from datetime import date

from entreprises.forms import EntrepriseQualificationForm
from entreprises.models import CaracteristiquesAnnuelles


def test_ignore_bilan_et_ca_consolides_lorsque_pas_de_comptes_consolides():
    data = {
        "date_cloture_exercice": date(2022, 12, 31),
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "effectif_permanent": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "effectif_outre_mer": CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_MOINS_DE_250,
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_ENTRE_700K_ET_12M,
        "tranche_bilan": CaracteristiquesAnnuelles.BILAN_ENTRE_6M_ET_20M,
        "est_cotee": False,
        "appartient_groupe": True,
        "effectif_groupe": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "effectif_groupe_france": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "effectif_groupe_permanent": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "societe_mere_en_france": True,
        "comptes_consolides": False,
        "tranche_chiffre_affaires_consolide": CaracteristiquesAnnuelles.CA_ENTRE_700K_ET_12M,
        "tranche_bilan_consolide": CaracteristiquesAnnuelles.BILAN_ENTRE_6M_ET_20M,
        "bdese_accord": True,
        "systeme_management_energie": True,
    }

    form = EntrepriseQualificationForm(data=data)

    assert form.is_valid(), form.errors
    assert form.cleaned_data["tranche_chiffre_affaires_consolide"] is None
    assert form.cleaned_data["tranche_bilan_consolide"] is None


def test_ignore_effectifs_groupe_societe_mere_et_comptes_consolides_lorsque_pas_de_groupe():
    data = {
        "date_cloture_exercice": date(2022, 12, 31),
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "effectif_permanent": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "effectif_outre_mer": CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_MOINS_DE_250,
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_ENTRE_700K_ET_12M,
        "tranche_bilan": CaracteristiquesAnnuelles.BILAN_ENTRE_6M_ET_20M,
        "est_cotee": False,
        "appartient_groupe": False,
        "effectif_groupe": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "effectif_groupe_france": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "effectif_groupe_permanent": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "est_societe_mere": True,
        "societe_mere_en_france": True,
        "comptes_consolides": True,
        "tranche_chiffre_affaires_consolide": CaracteristiquesAnnuelles.CA_ENTRE_700K_ET_12M,
        "tranche_bilan_consolide": CaracteristiquesAnnuelles.BILAN_ENTRE_6M_ET_20M,
        "bdese_accord": True,
        "systeme_management_energie": True,
    }

    form = EntrepriseQualificationForm(data=data)

    assert form.is_valid(), form.errors
    assert form.cleaned_data["effectif_groupe"] is None
    assert form.cleaned_data["effectif_groupe_france"] is None
    assert form.cleaned_data["effectif_groupe_permanent"] is None
    assert form.cleaned_data["est_societe_mere"] is None
    assert form.cleaned_data["societe_mere_en_france"] is None
    assert form.cleaned_data["comptes_consolides"] is None
    assert form.cleaned_data["tranche_chiffre_affaires_consolide"] is None
    assert form.cleaned_data["tranche_bilan_consolide"] is None


def test_erreur_si_appartient_groupe_sans_effectif_groupe():
    data = {
        "date_cloture_exercice": date(2022, 12, 31),
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "effectif_permanent": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "effectif_outre_mer": CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_MOINS_DE_250,
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_ENTRE_700K_ET_12M,
        "tranche_bilan": CaracteristiquesAnnuelles.BILAN_ENTRE_6M_ET_20M,
        "est_cotee": False,
        "appartient_groupe": True,
        "effectif_groupe": "",
        "effectif_groupe_france": "",
        "effectif_groupe_permanent": "",
        "societe_mere_en_france": True,
        "comptes_consolides": False,
        "tranche_chiffre_affaires_consolide": "",
        "tranche_bilan_consolide": "",
        "bdese_accord": True,
        "systeme_management_energie": True,
    }

    form = EntrepriseQualificationForm(data=data)

    assert not form.is_valid()
    assert (
        form.errors["effectif_groupe"][0]
        == "Ce champ est obligatoire lorsque l'entreprise appartient à un groupe"
    )
    assert (
        form.errors["effectif_groupe_france"][0]
        == "Ce champ est obligatoire lorsque l'entreprise appartient à un groupe"
    )
    assert (
        form.errors["effectif_groupe_permanent"][0]
        == "Ce champ est obligatoire lorsque l'entreprise appartient à un groupe"
    )


def test_erreur_si_comptes_consolides_sans_bilan_consolide():
    data = {
        "date_cloture_exercice": date(2022, 12, 31),
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "effectif_outre_mer": CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_MOINS_DE_250,
        "effectif_permanent": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_ENTRE_700K_ET_12M,
        "tranche_bilan": CaracteristiquesAnnuelles.BILAN_ENTRE_6M_ET_20M,
        "est_cotee": False,
        "appartient_groupe": True,
        "effectif_groupe": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "effectif_groupe_france": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "effectif_groupe_permanent": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "societe_mere_en_france": True,
        "comptes_consolides": True,
        "tranche_chiffre_affaires_consolide": CaracteristiquesAnnuelles.CA_ENTRE_700K_ET_12M,
        "tranche_bilan_consolide": "",
        "bdese_accord": True,
        "systeme_management_energie": True,
    }

    form = EntrepriseQualificationForm(data=data)

    assert not form.is_valid()
    assert (
        form.errors["tranche_bilan_consolide"][0]
        == "Ce champ est obligatoire lorsque les comptes sont consolidés"
    )


def test_erreur_si_comptes_consolides_sans_ca_consolide():
    data = {
        "date_cloture_exercice": date(2022, 12, 31),
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "effectif_outre_mer": CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_MOINS_DE_250,
        "effectif_permanent": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_ENTRE_700K_ET_12M,
        "tranche_bilan": CaracteristiquesAnnuelles.BILAN_ENTRE_6M_ET_20M,
        "est_cotee": False,
        "appartient_groupe": True,
        "effectif_groupe": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "effectif_groupe_france": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "effectif_groupe_permanent": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "societe_mere_en_france": True,
        "comptes_consolides": True,
        "tranche_chiffre_affaires_consolide": "",
        "tranche_bilan_consolide": CaracteristiquesAnnuelles.BILAN_ENTRE_6M_ET_20M,
        "bdese_accord": True,
        "systeme_management_energie": True,
    }

    form = EntrepriseQualificationForm(data=data)

    assert not form.is_valid()
    assert (
        form.errors["tranche_chiffre_affaires_consolide"][0]
        == "Ce champ est obligatoire lorsque les comptes sont consolidés"
    )
