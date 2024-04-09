from datetime import date

import pytest

from entreprises.forms import EntrepriseQualificationForm
from entreprises.forms import est_superieur
from entreprises.models import CaracteristiquesAnnuelles


def test_ignore_bilan_et_ca_consolides_lorsque_pas_de_comptes_consolides():
    data = {
        "date_cloture_exercice": date(2022, 12, 31),
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "effectif_permanent": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "effectif_outre_mer": CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_MOINS_DE_250,
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
        "tranche_bilan": CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
        "est_cotee": False,
        "appartient_groupe": True,
        "effectif_groupe": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "effectif_groupe_france": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "effectif_groupe_permanent": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "societe_mere_en_france": True,
        "comptes_consolides": False,
        "tranche_chiffre_affaires_consolide": CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
        "tranche_bilan_consolide": CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
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
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
        "tranche_bilan": CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
        "est_cotee": False,
        "appartient_groupe": False,
        "effectif_groupe": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "effectif_groupe_france": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "effectif_groupe_permanent": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "est_societe_mere": True,
        "societe_mere_en_france": True,
        "comptes_consolides": True,
        "tranche_chiffre_affaires_consolide": CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
        "tranche_bilan_consolide": CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
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
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
        "tranche_bilan": CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
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
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
        "tranche_bilan": CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
        "est_cotee": False,
        "appartient_groupe": True,
        "effectif_groupe": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "effectif_groupe_france": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "effectif_groupe_permanent": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "societe_mere_en_france": True,
        "comptes_consolides": True,
        "tranche_chiffre_affaires_consolide": CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
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
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
        "tranche_bilan": CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
        "est_cotee": False,
        "appartient_groupe": True,
        "effectif_groupe": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "effectif_groupe_france": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "effectif_groupe_permanent": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "societe_mere_en_france": True,
        "comptes_consolides": True,
        "tranche_chiffre_affaires_consolide": "",
        "tranche_bilan_consolide": CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        "bdese_accord": True,
        "systeme_management_energie": True,
    }

    form = EntrepriseQualificationForm(data=data)

    assert not form.is_valid()
    assert (
        form.errors["tranche_chiffre_affaires_consolide"][0]
        == "Ce champ est obligatoire lorsque les comptes sont consolidés"
    )


def test_erreur_si_les_effectifs_permanents_sont_superieurs_aux_effectifs():
    data = {
        "date_cloture_exercice": date(2022, 12, 31),
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "effectif_outre_mer": CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_MOINS_DE_250,
        "effectif_permanent": CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
        "tranche_bilan": CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
        "est_cotee": False,
        "appartient_groupe": True,
        "effectif_groupe": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "effectif_groupe_france": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "effectif_groupe_permanent": CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        "societe_mere_en_france": True,
        "comptes_consolides": False,
        "bdese_accord": True,
        "systeme_management_energie": True,
    }

    form = EntrepriseQualificationForm(data=data)

    assert not form.is_valid()
    assert (
        form.errors["effectif_permanent"][0]
        == "L'effectif permanent ne peut pas être supérieur à l'effectif"
    )
    assert (
        form.errors["effectif_groupe_permanent"][0]
        == "L'effectif permanent du groupe ne peut pas être supérieur à l'effectif du groupe international"
    )


def test_erreur_si_effectif_outre_mer_superieur_a_effectif():
    data = {
        "date_cloture_exercice": date(2022, 12, 31),
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "effectif_outre_mer": CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_250_ET_PLUS,
        "effectif_permanent": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
        "tranche_bilan": CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
        "est_cotee": False,
        "appartient_groupe": False,
        "bdese_accord": True,
        "systeme_management_energie": True,
    }

    form = EntrepriseQualificationForm(data=data)

    assert not form.is_valid()
    assert (
        form.errors["effectif_outre_mer"][0]
        == "L'effectif outre-mer ne peut pas être supérieur à l'effectif"
    )


def test_erreur_si_effectif_france_superieur_a_effectif_international():
    data = {
        "date_cloture_exercice": date(2022, 12, 31),
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "effectif_outre_mer": CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_MOINS_DE_250,
        "effectif_permanent": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
        "tranche_bilan": CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
        "est_cotee": False,
        "appartient_groupe": True,
        "effectif_groupe": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "effectif_groupe_france": CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        "effectif_groupe_permanent": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "societe_mere_en_france": True,
        "comptes_consolides": False,
        "bdese_accord": True,
        "systeme_management_energie": True,
    }

    form = EntrepriseQualificationForm(data=data)

    assert not form.is_valid()
    assert (
        form.errors["effectif_groupe_france"][0]
        == "L'effectif du groupe France ne peut pas être supérieur à l'effectif du groupe international"
    )


def test_erreur_si_effectifs_superieurs_a_effectifs_groupe():
    data = {
        "date_cloture_exercice": date(2022, 12, 31),
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "effectif_outre_mer": CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_MOINS_DE_250,
        "effectif_permanent": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
        "tranche_bilan": CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
        "est_cotee": False,
        "appartient_groupe": True,
        "effectif_groupe": CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50,
        "effectif_groupe_france": CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50,
        "effectif_groupe_permanent": CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50,
        "societe_mere_en_france": True,
        "comptes_consolides": False,
        "bdese_accord": True,
        "systeme_management_energie": True,
    }

    form = EntrepriseQualificationForm(data=data)

    assert not form.is_valid()
    assert (
        form.errors["effectif_groupe"][0]
        == "L'effectif du groupe ne peut pas être inférieur à l'effectif"
    )
    assert (
        form.errors["effectif_groupe_permanent"][0]
        == "L'effectif permanent du groupe ne peut pas être inférieur à l'effectif permanent"
    )


def test_ok_si_effectifs_inferieurs_ou_egaux_a_effectifs_groupe():
    data = {
        "date_cloture_exercice": date(2022, 12, 31),
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499,
        "effectif_outre_mer": CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_MOINS_DE_250,
        "effectif_permanent": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499,
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
        "tranche_bilan": CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
        "est_cotee": False,
        "appartient_groupe": True,
        "effectif_groupe": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_499,
        "effectif_groupe_france": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_499,
        "effectif_groupe_permanent": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_499,
        "societe_mere_en_france": True,
        "comptes_consolides": False,
        "bdese_accord": True,
        "systeme_management_energie": True,
    }

    form = EntrepriseQualificationForm(data=data)

    assert form.is_valid(), form.errors


def test_erreur_si_est_societe_mere_en_France_avec_un_effectif_superieur_a_effectif_groupe_france():
    data = {
        "date_cloture_exercice": date(2022, 12, 31),
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "effectif_outre_mer": CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_MOINS_DE_250,
        "effectif_permanent": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
        "tranche_bilan": CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
        "est_cotee": False,
        "appartient_groupe": True,
        "est_societe_mere": True,
        "societe_mere_en_france": True,
        "effectif_groupe": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "effectif_groupe_france": CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50,
        "effectif_groupe_permanent": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "comptes_consolides": False,
        "bdese_accord": True,
        "systeme_management_energie": True,
    }

    form = EntrepriseQualificationForm(data=data)

    assert not form.is_valid()
    assert (
        form.errors["effectif_groupe_france"][0]
        == "L'effectif du groupe France ne peut pas être inférieur à l'effectif si vous êtes la société mère du groupe et en France"
    )


def test_sans_interet_public_force_non_cotee():
    data = {
        "date_cloture_exercice": date(2022, 12, 31),
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "effectif_permanent": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "effectif_outre_mer": CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_MOINS_DE_250,
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
        "tranche_bilan": CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
        "est_cotee": True,
        "est_interet_public": False,
        "appartient_groupe": False,
        "bdese_accord": True,
        "systeme_management_energie": True,
    }

    form = EntrepriseQualificationForm(data=data)

    assert form.is_valid(), form.errors
    assert form.cleaned_data["est_interet_public"] is False
    assert form.cleaned_data["est_cotee"] is False


@pytest.mark.parametrize(
    "effectif", [effectif for effectif, _ in CaracteristiquesAnnuelles.EFFECTIF_CHOICES]
)
def test_est_superieur(effectif):
    assert not est_superieur(effectif, CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS)
    if effectif != CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS:
        assert est_superieur(CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS, effectif)
