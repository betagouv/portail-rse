import pytest

from entreprises.models import CaracteristiquesAnnuelles
from habilitations.models import attach_user_to_entreprise
from reglementations.views.base import ReglementationStatus
from reglementations.views.bges import BGESReglementation


def test_bges_reglementation_info():
    info = BGESReglementation.info()

    assert info["title"] == "BGES et plan de transition"

    assert (
        info["description"]
        == "Le Bilan GES réglementaire a vocation à contribuer à la mise en œuvre de la stratégie de réduction des émissions de GES des entreprises. Un plan de transition est obligatoirement joint à ce bilan. Il vise à réduire les émissions de gaz à effet de serre et présente les objectifs, moyens et actions envisagées à cette fin ainsi que, le cas échéant, les actions mises en œuvre lors du précédent bilan. Ils sont mis à jour tous les quatre ans."
    )
    assert info["more_info_url"] == "https://bilans-ges.ademe.fr/"


@pytest.mark.parametrize(
    "effectif",
    [
        CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499,
    ],
)
def test_calcule_le_statut_si_moins_de_500_employes(
    effectif, entreprise_factory, alice
):
    entreprise = entreprise_factory(effectif=effectif)
    attach_user_to_entreprise(alice, entreprise, "Présidente")

    reglementation = BGESReglementation(entreprise).calculate_status(
        entreprise.caracteristiques_actuelles(), alice
    )

    assert reglementation.status == ReglementationStatus.STATUS_NON_SOUMIS
    assert (
        reglementation.status_detail == "Vous n'êtes pas soumis à cette réglementation"
    )
    assert reglementation.primary_action.url == "https://bilans-ges.ademe.fr/bilans"
    assert (
        reglementation.primary_action.title == "Consulter les Bilans GES sur Bilans GES"
    )
    assert reglementation.primary_action.external


def test_calcule_le_statut_si_plus_de_500_employes(entreprise_factory, alice):
    entreprise = entreprise_factory(
        effectif=CaracteristiquesAnnuelles.EFFECTIF_500_ET_PLUS
    )
    attach_user_to_entreprise(alice, entreprise, "Présidente")

    reglementation = BGESReglementation(entreprise).calculate_status(
        entreprise.caracteristiques_actuelles(), alice
    )

    assert reglementation.status == ReglementationStatus.STATUS_SOUMIS
    assert (
        reglementation.status_detail
        == "Vous êtes soumis à cette réglementation car votre effectif est supérieur à 500 salariés."
    )
    assert (
        reglementation.primary_action.url
        == "https://bilans-ges.ademe.fr/bilans/comment-publier"
    )
    assert reglementation.primary_action.title == "Publier mon Bilan GES"
    assert reglementation.primary_action.external


def test_calcule_le_statut_avec_plus_de_250_employes_outre_mer(
    entreprise_factory, alice
):
    entreprise = entreprise_factory(
        effectif=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        effectif_outre_mer=CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_250_ET_PLUS,
    )
    attach_user_to_entreprise(alice, entreprise, "Présidente")

    reglementation = BGESReglementation(entreprise).calculate_status(
        entreprise.caracteristiques_actuelles(), alice
    )

    assert reglementation.status == ReglementationStatus.STATUS_SOUMIS
    assert (
        reglementation.status_detail
        == "Vous êtes soumis à cette réglementation car votre effectif outre-mer est supérieur à 250 salariés."
    )
    assert reglementation.primary_action.title == "Publier mon Bilan GES"
