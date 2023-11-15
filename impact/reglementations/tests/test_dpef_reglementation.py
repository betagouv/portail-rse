import pytest
from django.urls import reverse

from entreprises.models import CaracteristiquesAnnuelles
from reglementations.views.dpef import DPEFReglementation


def test_dpef_reglementation_info():
    info = DPEFReglementation.info()

    assert info["title"] == "Déclaration de Performance Extra-Financière"

    assert (
        info["description"]
        == """La Déclaration de Performance Extra-Financière (dite "DPEF") est un document par l'intermédiaire duquel une entreprise détaille les implications sociales, environnementales et sociétales de sa performance et de ses activités, ainsi que son mode de gouvernance."""
    )
    assert info["more_info_url"] == reverse("reglementations:fiche_dpef")


@pytest.mark.parametrize(
    "effectif_permanent",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
    ],
)
def test_soumis_si_effectif_permanent_et_bilan_suffisants(
    effectif_permanent, entreprise_factory
):
    entreprise = entreprise_factory(
        effectif_permanent=effectif_permanent,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_700K,
    )

    soumis = DPEFReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    criteres_remplis = DPEFReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert soumis
    assert criteres_remplis == [
        "votre effectif permanent est supérieur à 500 salariés",
        "votre bilan est supérieur à 100M€",
    ]


@pytest.mark.parametrize(
    "effectif_permanent",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
    ],
)
def test_soumis_si_effectif_permanent_et_ca_suffisants(
    effectif_permanent, entreprise_factory
):
    entreprise = entreprise_factory(
        effectif_permanent=effectif_permanent,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_350K,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    )

    soumis = DPEFReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    criteres_remplis = DPEFReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert soumis
    assert criteres_remplis == [
        "votre effectif permanent est supérieur à 500 salariés",
        "votre chiffre d'affaires est supérieur à 100M€",
    ]


@pytest.mark.parametrize(
    "effectif_permanent",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
    ],
)
def test_soumis_si_effectif_permanent_bilan_et_ca_suffisants(
    effectif_permanent, entreprise_factory
):
    entreprise = entreprise_factory(
        effectif_permanent=effectif_permanent,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    )

    soumis = DPEFReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    criteres_remplis = DPEFReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert soumis
    assert criteres_remplis == [
        "votre effectif permanent est supérieur à 500 salariés",
        "votre bilan est supérieur à 100M€",
        "votre chiffre d'affaires est supérieur à 100M€",
    ]


@pytest.mark.parametrize(
    "effectif_permanent",
    [
        CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_299,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499,
    ],
)
def test_non_soumis_si_effectif_permanent_insuffisant(
    effectif_permanent, entreprise_factory
):
    entreprise = entreprise_factory(
        effectif_permanent=effectif_permanent,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    )

    soumis = DPEFReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert not soumis


@pytest.mark.parametrize(
    "bilan",
    [
        CaracteristiquesAnnuelles.BILAN_MOINS_DE_350K,
        CaracteristiquesAnnuelles.BILAN_ENTRE_350K_ET_6M,
        CaracteristiquesAnnuelles.BILAN_ENTRE_6M_ET_20M,
        CaracteristiquesAnnuelles.BILAN_ENTRE_20M_ET_43M,
        CaracteristiquesAnnuelles.BILAN_ENTRE_43M_ET_100M,
    ],
)
@pytest.mark.parametrize(
    "ca",
    [
        CaracteristiquesAnnuelles.CA_MOINS_DE_700K,
        CaracteristiquesAnnuelles.CA_ENTRE_700K_ET_12M,
        CaracteristiquesAnnuelles.CA_ENTRE_12M_ET_40M,
        CaracteristiquesAnnuelles.CA_ENTRE_40M_ET_50M,
        CaracteristiquesAnnuelles.CA_ENTRE_50M_ET_100M,
    ],
)
def test_non_soumis_si_bilan_et_ca_insuffisants(bilan, ca, entreprise_factory):
    entreprise = entreprise_factory(
        effectif_permanent=CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        tranche_bilan=bilan,
        tranche_chiffre_affaires=ca,
    )

    soumis = DPEFReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert not soumis


@pytest.mark.parametrize(
    "effectif_groupe_permanent",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
    ],
)
def test_soumis_si_effectif_groupe_permanent_et_bilan_consolide_suffisants(
    effectif_groupe_permanent, entreprise_factory
):
    entreprise = entreprise_factory(
        appartient_groupe=True,
        comptes_consolides=True,
        effectif_groupe_permanent=effectif_groupe_permanent,
        tranche_bilan_consolide=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        tranche_chiffre_affaires_consolide=CaracteristiquesAnnuelles.CA_MOINS_DE_700K,
    )

    soumis = DPEFReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    criteres_remplis = DPEFReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert soumis
    assert criteres_remplis == [
        "l'effectif permanent du groupe est supérieur à 500 salariés",
        "votre bilan consolidé est supérieur à 100M€",
    ]


@pytest.mark.parametrize(
    "effectif_groupe_permanent",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
    ],
)
def test_soumis_si_effectif_groupe_permanent_et_ca_consolide_suffisants(
    effectif_groupe_permanent, entreprise_factory
):
    entreprise = entreprise_factory(
        appartient_groupe=True,
        comptes_consolides=True,
        effectif_groupe_permanent=effectif_groupe_permanent,
        tranche_bilan_consolide=CaracteristiquesAnnuelles.BILAN_MOINS_DE_350K,
        tranche_chiffre_affaires_consolide=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    )

    soumis = DPEFReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    criteres_remplis = DPEFReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert soumis
    assert criteres_remplis == [
        "l'effectif permanent du groupe est supérieur à 500 salariés",
        "votre chiffre d'affaires consolidé est supérieur à 100M€",
    ]


@pytest.mark.parametrize(
    "effectif_groupe_permanent",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
    ],
)
def test_soumis_si_effectif_groupe_permanent_bilan_et_ca_consolides_suffisants(
    effectif_groupe_permanent, entreprise_factory
):
    entreprise = entreprise_factory(
        appartient_groupe=True,
        comptes_consolides=True,
        effectif_groupe_permanent=effectif_groupe_permanent,
        tranche_bilan_consolide=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        tranche_chiffre_affaires_consolide=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    )

    soumis = DPEFReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    criteres_remplis = DPEFReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert soumis
    assert criteres_remplis == [
        "l'effectif permanent du groupe est supérieur à 500 salariés",
        "votre bilan consolidé est supérieur à 100M€",
        "votre chiffre d'affaires consolidé est supérieur à 100M€",
    ]


@pytest.mark.parametrize(
    "effectif_groupe_permanent",
    [
        CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_299,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499,
    ],
)
def test_non_soumis_si_effectif_groupe_permanent_insuffisant(
    effectif_groupe_permanent, entreprise_factory
):
    entreprise = entreprise_factory(
        appartient_groupe=True,
        comptes_consolides=True,
        effectif_groupe_permanent=effectif_groupe_permanent,
        tranche_bilan_consolide=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        tranche_chiffre_affaires_consolide=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    )

    soumis = DPEFReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert not soumis


@pytest.mark.parametrize(
    "effectif_groupe_permanent",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
    ],
)
def test_non_soumis_si_effectif_insuffisant_et_effectif_groupe_permanent_suffisant_mais_pas_de_comptes_consolides(
    effectif_groupe_permanent, entreprise_factory
):
    entreprise = entreprise_factory(
        appartient_groupe=True,
        comptes_consolides=False,
        effectif_permanent=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50,
        effectif_groupe_permanent=effectif_groupe_permanent,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
    )

    soumis = DPEFReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert not soumis


@pytest.mark.parametrize(
    "effectif_permanent",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
    ],
)
@pytest.mark.parametrize(
    "bilan",
    [
        CaracteristiquesAnnuelles.BILAN_ENTRE_20M_ET_43M,
        CaracteristiquesAnnuelles.BILAN_ENTRE_43M_ET_100M,
        CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
    ],
)
def test_soumis_si_societe_cotee_et_effectif_permanent_et_bilan_suffisants(
    effectif_permanent, bilan, entreprise_factory
):
    entreprise = entreprise_factory(
        est_cotee=True,
        effectif_permanent=effectif_permanent,
        tranche_bilan=bilan,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_700K,
    )

    soumis = DPEFReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    criteres_remplis = DPEFReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert soumis
    assert criteres_remplis == [
        "votre sociétée est cotée sur un marché réglementé",
        "votre effectif permanent est supérieur à 500 salariés",
        "votre bilan est supérieur à 20M€",
    ]


@pytest.mark.parametrize(
    "effectif_permanent",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
    ],
)
@pytest.mark.parametrize(
    "ca",
    [
        CaracteristiquesAnnuelles.CA_ENTRE_40M_ET_50M,
        CaracteristiquesAnnuelles.CA_ENTRE_50M_ET_100M,
        CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    ],
)
def test_soumis_si_societe_cotee_et_effectif_permanent_et_ca_suffisants(
    effectif_permanent, ca, entreprise_factory
):
    entreprise = entreprise_factory(
        est_cotee=True,
        effectif_permanent=effectif_permanent,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_350K,
        tranche_chiffre_affaires=ca,
    )

    soumis = DPEFReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    criteres_remplis = DPEFReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert soumis
    assert criteres_remplis == [
        "votre sociétée est cotée sur un marché réglementé",
        "votre effectif permanent est supérieur à 500 salariés",
        "votre chiffre d'affaires est supérieur à 40M€",
    ]


@pytest.mark.parametrize(
    "effectif_permanent",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
    ],
)
@pytest.mark.parametrize(
    "bilan",
    [
        CaracteristiquesAnnuelles.BILAN_ENTRE_20M_ET_43M,
        CaracteristiquesAnnuelles.BILAN_ENTRE_43M_ET_100M,
        CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
    ],
)
@pytest.mark.parametrize(
    "ca",
    [
        CaracteristiquesAnnuelles.CA_ENTRE_40M_ET_50M,
        CaracteristiquesAnnuelles.CA_ENTRE_50M_ET_100M,
        CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    ],
)
def test_soumis_si_societe_cotee_et_effectif_permanent_bilan_et_ca_suffisants(
    effectif_permanent, bilan, ca, entreprise_factory
):
    entreprise = entreprise_factory(
        est_cotee=True,
        effectif_permanent=effectif_permanent,
        tranche_bilan=bilan,
        tranche_chiffre_affaires=ca,
    )

    soumis = DPEFReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    criteres_remplis = DPEFReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert soumis
    assert criteres_remplis == [
        "votre sociétée est cotée sur un marché réglementé",
        "votre effectif permanent est supérieur à 500 salariés",
        "votre bilan est supérieur à 20M€",
        "votre chiffre d'affaires est supérieur à 40M€",
    ]


@pytest.mark.parametrize(
    "effectif_groupe_permanent",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
    ],
)
@pytest.mark.parametrize(
    "bilan",
    [
        CaracteristiquesAnnuelles.BILAN_ENTRE_20M_ET_43M,
        CaracteristiquesAnnuelles.BILAN_ENTRE_43M_ET_100M,
        CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
    ],
)
def test_soumis_si_societe_cotee_et_effectif_groupe_permanent_et_bilan_consolide_suffisants(
    effectif_groupe_permanent, bilan, entreprise_factory
):
    entreprise = entreprise_factory(
        est_cotee=True,
        appartient_groupe=True,
        comptes_consolides=True,
        effectif_groupe_permanent=effectif_groupe_permanent,
        tranche_bilan_consolide=bilan,
        tranche_chiffre_affaires_consolide=CaracteristiquesAnnuelles.CA_MOINS_DE_700K,
    )

    soumis = DPEFReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    criteres_remplis = DPEFReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert soumis
    assert criteres_remplis == [
        "votre sociétée est cotée sur un marché réglementé",
        "l'effectif permanent du groupe est supérieur à 500 salariés",
        "votre bilan consolidé est supérieur à 20M€",
    ]


@pytest.mark.parametrize(
    "effectif_groupe_permanent",
    [
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
    ],
)
@pytest.mark.parametrize(
    "ca",
    [
        CaracteristiquesAnnuelles.CA_ENTRE_40M_ET_50M,
        CaracteristiquesAnnuelles.CA_ENTRE_50M_ET_100M,
        CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    ],
)
def test_soumis_si_effectif_groupe_permanent_et_ca_consolide_suffisants(
    effectif_groupe_permanent, ca, entreprise_factory
):
    entreprise = entreprise_factory(
        est_cotee=True,
        appartient_groupe=True,
        comptes_consolides=True,
        effectif_groupe_permanent=effectif_groupe_permanent,
        tranche_bilan_consolide=CaracteristiquesAnnuelles.BILAN_MOINS_DE_350K,
        tranche_chiffre_affaires_consolide=ca,
    )

    soumis = DPEFReglementation.est_soumis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    criteres_remplis = DPEFReglementation.criteres_remplis(
        entreprise.dernieres_caracteristiques_qualifiantes
    )

    assert soumis
    assert criteres_remplis == [
        "votre sociétée est cotée sur un marché réglementé",
        "l'effectif permanent du groupe est supérieur à 500 salariés",
        "votre chiffre d'affaires consolidé est supérieur à 40M€",
    ]
