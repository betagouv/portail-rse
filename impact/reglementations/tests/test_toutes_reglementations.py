import pytest

from entreprises.models import CaracteristiquesAnnuelles
from reglementations.views import REGLEMENTATIONS
from reglementations.views.base import InsuffisammentQualifieeError
from reglementations.views.base import ReglementationStatus
from reglementations.views.vsme import VSMEReglementation


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
