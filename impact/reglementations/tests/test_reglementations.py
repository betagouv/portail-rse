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
from reglementations.views.bdese import BDESEReglementation
from reglementations.views.bges import BGESReglementation
from reglementations.views.dispositif_alerte import DispositifAlerteReglementation
from reglementations.views.dispositif_anticorruption import DispositifAntiCorruption
from reglementations.views.dpef import DPEFReglementation
from reglementations.views.index_egapro import IndexEgaproReglementation

REGLEMENTATIONS = (
    BDESEReglementation,
    IndexEgaproReglementation,
    DispositifAlerteReglementation,
    BGESReglementation,
    AuditEnergetiqueReglementation,
    DispositifAntiCorruption,
    DPEFReglementation,
)


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


def test_reglementations_for_entreprise_with_authenticated_user(client, entreprise):
    client.force_login(entreprise.users.first())

    response = client.get(f"/reglementations/{entreprise.siren}")

    assert response.status_code == 200

    content = response.content.decode("utf-8")
    context = response.context
    assert context["entreprise"] == entreprise
    reglementations = context["reglementations"]
    for index, REGLEMENTATION in enumerate(REGLEMENTATIONS):
        assert reglementations[index]["status"] == REGLEMENTATION.calculate_status(
            entreprise.dernieres_caracteristiques_qualifiantes, entreprise.users.first()
        )
    for reglementation in reglementations:
        assert reglementation["status"].status_detail in content


def test_reglementations_for_entreprise_with_authenticated_user_and_multiple_entreprises(
    client, entreprise_factory, alice
):
    entreprise1 = entreprise_factory(siren="000000001")
    entreprise2 = entreprise_factory(siren="000000002")
    attach_user_to_entreprise(alice, entreprise1, "Présidente")
    attach_user_to_entreprise(alice, entreprise2, "Présidente")
    client.force_login(alice)

    response = client.get(f"/reglementations/{entreprise1.siren}")

    assert response.status_code == 200

    content = response.content.decode("utf-8")
    context = response.context
    assert context["entreprise"] == entreprise1
    reglementations = context["reglementations"]
    for index, REGLEMENTATION in enumerate(REGLEMENTATIONS):
        assert reglementations[index]["status"] == REGLEMENTATION.calculate_status(
            entreprise1.dernieres_caracteristiques_qualifiantes, alice
        )
    for reglementation in reglementations:
        assert reglementation["status"].status_detail in content

    response = client.get(f"/reglementations/{entreprise2.siren}")

    assert response.status_code == 200

    content = response.content.decode("utf-8")
    context = response.context
    assert context["entreprise"] == entreprise2
    reglementations = context["reglementations"]
    for index, REGLEMENTATION in enumerate(REGLEMENTATIONS):
        assert reglementations[index]["status"] == REGLEMENTATION.calculate_status(
            entreprise2.dernieres_caracteristiques_qualifiantes, alice
        )
    for reglementation in reglementations:
        assert reglementation["status"].status_detail in content


def test_reglementations_for_entreprise_non_qualifiee_redirect_to_qualification_page(
    client, alice, entreprise_non_qualifiee, mock_api_recherche_entreprises
):
    attach_user_to_entreprise(alice, entreprise_non_qualifiee, "Présidente")
    client.force_login(alice)

    response = client.get(
        f"/reglementations/{entreprise_non_qualifiee.siren}", follow=True
    )

    assert response.status_code == 200
    url = f"/entreprises/{entreprise_non_qualifiee.siren}"
    assert response.redirect_chain == [(url, 302)]


def test_reglementations_for_entreprise_qualifiee_dans_le_passe(
    client, date_cloture_dernier_exercice, entreprise
):
    with freeze_time(date_cloture_dernier_exercice + timedelta(days=367)):
        client.force_login(entreprise.users.first())
        response = client.get(f"/reglementations/{entreprise.siren}")

    assert response.status_code == 200
    content = html.unescape(response.content.decode("utf-8"))
    assert (
        f"Les réglementations sont basées sur des informations de l'exercice {date_cloture_dernier_exercice.year}."
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

    reglementations = calcule_reglementations(
        entreprise.dernieres_caracteristiques_qualifiantes, AnonymousUser()
    )

    assert [reglementation["reglementation"] for reglementation in reglementations] == [
        IndexEgaproReglementation,
        BGESReglementation,
        DispositifAntiCorruption,
        BDESEReglementation,
        DispositifAlerteReglementation,
        AuditEnergetiqueReglementation,
        DPEFReglementation,
    ]
