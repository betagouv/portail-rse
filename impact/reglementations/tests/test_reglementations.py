import pytest

from entreprises.models import CaracteristiquesAnnuelles
from reglementations.utils import VSMEReglementation
from reglementations.views import REGLEMENTATIONS
from reglementations.views.base import InsuffisammentQualifieeError
from reglementations.views.base import ReglementationStatus


def test_les_reglementations_obligatoires_levent_une_exception_si_les_caracteristiques_sont_vides(
    entreprise_non_qualifiee,
):
    caracteristiques = CaracteristiquesAnnuelles(entreprise=entreprise_non_qualifiee)
    REGLEMENTATIONS_RECOMMANDEES = [VSMEReglementation]

    for reglementation in REGLEMENTATIONS:
        if reglementation not in REGLEMENTATIONS_RECOMMANDEES:
            with pytest.raises(InsuffisammentQualifieeError):
                reglementation.est_soumis(caracteristiques)
            status = reglementation.calculate_status(caracteristiques)
            assert status.status == ReglementationStatus.STATUS_INCALCULABLE


def test_reglementations_avec_utilisateur_authentifié(
    client, entreprise_factory, alice
):
    entreprise = entreprise_factory(
        effectif=CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        utilisateur=alice,
    )
    client.force_login(alice)

    response = client.get(f"/tableau-de-bord/{entreprise.siren}/reglementations")

    assert response.status_code == 200

    content = response.content.decode("utf-8")
    context = response.context
    assert context["entreprise"] == entreprise
    reglementations = (
        context["reglementations_a_actualiser"]
        + context["reglementations_en_cours"]
        + context["reglementations_a_jour"]
        + context["autres_reglementations"]
    )
    assert len(reglementations) == len(REGLEMENTATIONS)
    for REGLEMENTATION in REGLEMENTATIONS:
        index = [
            reglementation["reglementation"] for reglementation in reglementations
        ].index(REGLEMENTATION)
        assert reglementations[index]["status"] == REGLEMENTATION.calculate_status(
            entreprise.dernieres_caracteristiques_qualifiantes
        )
