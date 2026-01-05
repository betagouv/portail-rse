from datetime import datetime

import pytest

import reglementations.views  # noqa
from entreprises.models import CaracteristiquesAnnuelles
from reglementations.models import RapportCSRD
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


def test_reglementations(client, entreprise_factory, alice):
    entreprise = entreprise_factory(
        effectif=CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,  # entreprise soumise à au moins une réglementation
        utilisateur=alice,
    )
    client.force_login(alice)

    response = client.get(f"/tableau-de-bord/{entreprise.siren}/reglementations/")

    assert response.status_code == 200

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


@pytest.mark.parametrize("reglementation", REGLEMENTATIONS)
def test_reglementation(reglementation, client, entreprise_factory, alice):
    entreprise = entreprise_factory(
        effectif=CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,  # entreprise soumise à au moins une réglementation
        utilisateur=alice,
    )
    status = reglementation.calculate_status(
        entreprise.dernieres_caracteristiques_qualifiantes
    )
    client.force_login(alice)

    response = client.get(
        f"/tableau-de-bord/{entreprise.siren}/reglementations/{reglementation.id}/"
    )

    assert response.status_code == 200
    context = response.context
    assert context["entreprise"] == entreprise
    assert context["reglementation"] == reglementation
    assert context["status"] == status


def test_reglementation_inexistante(client, entreprise_factory, alice):
    entreprise = entreprise_factory(utilisateur=alice)
    client.force_login(alice)

    response = client.get(f"/tableau-de-bord/{entreprise.siren}/reglementations/yolo/")

    assert response.status_code == 404


@pytest.mark.parametrize("reglementation", REGLEMENTATIONS)
def test_reglementation_sans_siren_redirige_vers_celle_de_l_entreprise_courante(
    reglementation, client, entreprise_factory, alice
):
    entreprise = entreprise_factory(utilisateur=alice)
    client.force_login(alice)

    response = client.get(f"/tableau-de-bord/reglementations/{reglementation.id}/")

    assert response.status_code == 302
    assert (
        response.url
        == f"/tableau-de-bord/{entreprise.siren}/reglementations/{reglementation.id}/"
    )


def test_reglementation_sur_la_csrd_fournit_la_csrd_en_cours_au_template_si_elle_existe(
    client, entreprise_factory, alice
):
    entreprise = entreprise_factory(
        effectif=CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,  # entreprise soumise à au moins une réglementation
        utilisateur=alice,
    )
    client.force_login(alice)

    response = client.get(f"/tableau-de-bord/{entreprise.siren}/reglementations/csrd/")

    assert response.status_code == 200
    context = response.context
    assert context["csrd"] is None

    rapport = RapportCSRD.objects.create(
        entreprise=entreprise,
        annee=datetime.now().year,
    )

    response = client.get(f"/tableau-de-bord/{entreprise.siren}/reglementations/csrd/")

    assert response.status_code == 200
    context = response.context
    assert context["csrd"] == rapport
