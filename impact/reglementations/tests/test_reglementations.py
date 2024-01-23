import html
from datetime import timedelta

import pytest
from django.contrib.auth.models import AnonymousUser
from freezegun import freeze_time

from api.tests.fixtures import mock_api_recherche_entreprises  # noqa
from entreprises.models import CaracteristiquesAnnuelles
from habilitations.models import attach_user_to_entreprise
from reglementations.views import calcule_reglementations
from reglementations.views.audit_energetique import AuditEnergetiqueReglementation
from reglementations.views.base import InsuffisammentQualifieeError
from reglementations.views.base import ReglementationStatus
from reglementations.views.bdese import BDESEReglementation
from reglementations.views.bges import BGESReglementation
from reglementations.views.dispositif_alerte import DispositifAlerteReglementation
from reglementations.views.dispositif_anticorruption import DispositifAntiCorruption
from reglementations.views.dpef import DPEFReglementation
from reglementations.views.index_egapro import IndexEgaproReglementation
from reglementations.views.plan_vigilance import PlanVigilanceReglementation

REGLEMENTATIONS = (
    BDESEReglementation,
    IndexEgaproReglementation,
    DispositifAlerteReglementation,
    BGESReglementation,
    AuditEnergetiqueReglementation,
    DispositifAntiCorruption,
    DPEFReglementation,
    PlanVigilanceReglementation,
)


def test_les_reglementations_levent_une_exception_si_les_caracteristiques_sont_vides(
    entreprise_non_qualifiee,
):
    caracteristiques = CaracteristiquesAnnuelles(entreprise=entreprise_non_qualifiee)

    for reglementation in REGLEMENTATIONS:
        with pytest.raises(InsuffisammentQualifieeError):
            reglementation.est_soumis(caracteristiques)
        status = reglementation.calculate_status(caracteristiques, AnonymousUser())
        assert status.status == ReglementationStatus.STATUS_INCALCULABLE


def test_fiches_reglementations_sont_publiques(client):
    templates = {
        "/reglementations/bdese": "reglementations/fiches/bdese.html",
        "/reglementations/index-egalite-professionnelle": "reglementations/fiches/index-egalite-professionnelle.html",
        "/reglementations/dispositif-alerte": "reglementations/fiches/dispositif-alerte.html",
        "/reglementations/bilan-ges": "reglementations/fiches/bilan-ges.html",
        "/reglementations/audit-energetique": "reglementations/fiches/audit-energetique.html",
        "/reglementations/dispositif-anticorruption": "reglementations/fiches/dispositif-anticorruption.html",
        "/reglementations/declaration-de-performance-extra-financiere": "reglementations/fiches/dpef.html",
        "/reglementations/rapport-durabilite-csrd": "reglementations/fiches/csrd.html",
        "/reglementations/plan-vigilance": "reglementations/fiches/plan-vigilance.html",
    }

    for url, template in templates.items():
        response = client.get(url)
        assert response.status_code == 200
        assert response.templates[0].name == template


@pytest.fixture
def entreprise(db, alice, entreprise_factory):
    entreprise = entreprise_factory(
        siren="000000001",
        denomination="Entreprise SAS",
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50,
    )
    attach_user_to_entreprise(alice, entreprise, "Présidente")
    return entreprise


def test_tableau_de_bord_avec_utilisateur_authentifié(client, entreprise):
    client.force_login(entreprise.users.first())

    response = client.get(f"/tableau-de-bord/{entreprise.siren}")

    assert response.status_code == 200

    content = response.content.decode("utf-8")
    context = response.context
    assert context["entreprise"] == entreprise
    reglementations = context["reglementations"]
    for REGLEMENTATION in REGLEMENTATIONS:
        REGLEMENTATION_STATUS = REGLEMENTATION.calculate_status(
            entreprise.dernieres_caracteristiques_qualifiantes, entreprise.users.first()
        )
        assert REGLEMENTATION_STATUS in [
            status
            for liste_de_reglementation_et_status in reglementations[
                REGLEMENTATION_STATUS.label
            ]
            for k, status in liste_de_reglementation_et_status.items()
            if k == "status"
        ]
    for status_label, reglementations_et_status in reglementations.items():
        for reglementation_et_status in reglementations_et_status:
            assert reglementation_et_status["status"].status_detail in content
            assert reglementation_et_status["status"].label == status_label


def test_tableau_de_bord_avec_utilisateur_authentifie_et_multiple_entreprises(
    client, entreprise_factory, alice
):
    entreprise1 = entreprise_factory(siren="000000001")
    entreprise2 = entreprise_factory(siren="000000002")
    attach_user_to_entreprise(alice, entreprise1, "Présidente")
    attach_user_to_entreprise(alice, entreprise2, "Présidente")
    client.force_login(alice)

    response = client.get(f"/tableau-de-bord/{entreprise1.siren}")

    assert response.status_code == 200

    content = response.content.decode("utf-8")
    context = response.context
    assert context["entreprise"] == entreprise1
    reglementations = context["reglementations"]
    for REGLEMENTATION in REGLEMENTATIONS:
        REGLEMENTATION_STATUS = REGLEMENTATION.calculate_status(
            entreprise1.dernieres_caracteristiques_qualifiantes, alice
        )
        assert REGLEMENTATION_STATUS in [
            status
            for liste_de_reglementation_et_status in reglementations[
                REGLEMENTATION_STATUS.label
            ]
            for k, status in liste_de_reglementation_et_status.items()
            if k == "status"
        ]
    for _, reglementations_et_status in reglementations.items():
        for reglementation_et_status in reglementations_et_status:
            assert reglementation_et_status["status"].status_detail in content

    response = client.get(f"/tableau-de-bord/{entreprise2.siren}")

    assert response.status_code == 200

    content = response.content.decode("utf-8")
    context = response.context
    assert context["entreprise"] == entreprise2
    reglementations = context["reglementations"]
    for REGLEMENTATION in REGLEMENTATIONS:
        REGLEMENTATION_STATUS = REGLEMENTATION.calculate_status(
            entreprise2.dernieres_caracteristiques_qualifiantes, alice
        )
        assert REGLEMENTATION_STATUS in [
            status
            for liste_de_reglementation_et_status in reglementations[
                REGLEMENTATION_STATUS.label
            ]
            for k, status in liste_de_reglementation_et_status.items()
            if k == "status"
        ]
    for _, reglementations_et_status in reglementations.items():
        for reglementation_et_status in reglementations_et_status:
            assert reglementation_et_status["status"].status_detail in content


def test_tableau_de_bord_entreprise_non_qualifiee_redirige_vers_la_qualification(
    client, alice, entreprise_non_qualifiee, mock_api_recherche_entreprises
):
    attach_user_to_entreprise(alice, entreprise_non_qualifiee, "Présidente")
    client.force_login(alice)

    response = client.get(
        f"/tableau-de-bord/{entreprise_non_qualifiee.siren}", follow=True
    )

    assert response.status_code == 200
    url = f"/entreprises/{entreprise_non_qualifiee.siren}"
    assert response.redirect_chain == [(url, 302)]


def test_tableau_de_bord_entreprise_qualifiee_dans_le_passe(
    client, date_cloture_dernier_exercice, entreprise
):
    with freeze_time(date_cloture_dernier_exercice + timedelta(days=367)):
        client.force_login(entreprise.users.first())
        response = client.get(f"/tableau-de-bord/{entreprise.siren}")

    assert response.status_code == 200
    content = html.unescape(response.content.decode("utf-8"))
    assert (
        f"Les réglementations affichées sont basées sur des informations de l'exercice comptable {date_cloture_dernier_exercice.year}."
        in content
    ), content


def test_calcule_reglementations_trie_les_statuts_soumis_en_premier(
    entreprise_factory, mocker
):
    entreprise = entreprise_factory()

    mocker.patch(
        "reglementations.views.bdese.BDESEReglementation.est_soumis",
        return_value=False,
    )
    mocker.patch(
        "reglementations.views.index_egapro.IndexEgaproReglementation.est_soumis",
        return_value=True,
    )
    mocker.patch(
        "reglementations.views.dispositif_alerte.DispositifAlerteReglementation.est_soumis",
        return_value=False,
    )
    mocker.patch(
        "reglementations.views.bges.BGESReglementation.est_soumis",
        return_value=True,
    )
    mocker.patch(
        "reglementations.views.audit_energetique.AuditEnergetiqueReglementation.est_soumis",
        return_value=False,
    )
    mocker.patch(
        "reglementations.views.dispositif_anticorruption.DispositifAntiCorruption.est_soumis",
        return_value=True,
    )
    mocker.patch(
        "reglementations.views.dpef.DPEFReglementation.est_soumis",
        return_value=False,
    )
    mocker.patch(
        "reglementations.views.plan_vigilance.PlanVigilanceReglementation.est_soumis",
        return_value=True,
    )

    reglementations = calcule_reglementations(
        entreprise.dernieres_caracteristiques_qualifiantes, AnonymousUser()
    )

    assert [reglementation["reglementation"] for reglementation in reglementations] == [
        IndexEgaproReglementation,
        BGESReglementation,
        DispositifAntiCorruption,
        PlanVigilanceReglementation,
        BDESEReglementation,
        DispositifAlerteReglementation,
        AuditEnergetiqueReglementation,
        DPEFReglementation,
    ]
