import html
from datetime import date
from datetime import datetime
from datetime import timedelta

import pytest
from freezegun import freeze_time

import reglementations.views  # noqa
from entreprises.models import CaracteristiquesAnnuelles
from habilitations.models import Habilitation
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


def test_reglementations_entreprise_non_qualifiee_redirige_vers_la_qualification(
    client, entreprise_non_qualifiee, alice
):
    Habilitation.ajouter(entreprise_non_qualifiee, alice, fonctions="Présidente")
    client.force_login(alice)

    url = f"/tableau-de-bord/{entreprise_non_qualifiee.siren}/reglementations/"
    response = client.get(url, follow=True)

    assert response.status_code == 200
    url = f"/entreprises/{entreprise_non_qualifiee.siren}"
    assert response.redirect_chain == [(url, 302)]

    content = html.unescape(response.content.decode("utf-8"))
    assert (
        f"Votre profil entreprise est incomplet ou doit être mis à jour suite à l'évolution d'une réglementation."
        in content
    ), content


def test_reglementations_entreprise_qualifiee_dans_le_passe(
    client, entreprise_factory, alice
):
    date_cloture_exercice = date(2024, 12, 31)
    entreprise = entreprise_factory(
        utilisateur=alice, date_cloture_exercice=date_cloture_exercice
    )

    url = f"/tableau-de-bord/{entreprise.siren}/reglementations/"
    with freeze_time(date_cloture_exercice + timedelta(days=367)):
        client.force_login(alice)
        response = client.get(url)

    assert response.status_code == 200
    content = html.unescape(response.content.decode("utf-8"))
    assert (
        f"Les informations affichées sont basées sur l'exercice comptable {date_cloture_exercice.year}."
        in content
    ), content


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


@pytest.mark.parametrize("reglementation", REGLEMENTATIONS)
def test_reglementation_entreprise_non_qualifiee_redirige_vers_la_qualification(
    reglementation, client, entreprise_non_qualifiee, alice
):
    Habilitation.ajouter(entreprise_non_qualifiee, alice, fonctions="Présidente")
    client.force_login(alice)

    url = f"/tableau-de-bord/{entreprise_non_qualifiee.siren}/reglementations/{reglementation.id}/"
    response = client.get(url, follow=True)

    assert response.status_code == 200
    url = f"/entreprises/{entreprise_non_qualifiee.siren}"
    assert response.redirect_chain == [(url, 302)]

    content = html.unescape(response.content.decode("utf-8"))
    assert (
        f"Votre profil entreprise est incomplet ou doit être mis à jour suite à l'évolution d'une réglementation."
        in content
    ), content


@pytest.mark.parametrize("reglementation", REGLEMENTATIONS)
def test_reglementation_entreprise_qualifiee_dans_le_passe(
    reglementation, client, entreprise_factory, alice
):
    date_cloture_exercice = date(2024, 12, 31)
    entreprise = entreprise_factory(
        utilisateur=alice, date_cloture_exercice=date_cloture_exercice
    )

    url = f"/tableau-de-bord/{entreprise.siren}/reglementations/{reglementation.id}/"
    with freeze_time(date_cloture_exercice + timedelta(days=367)):
        client.force_login(alice)
        response = client.get(url)

    assert response.status_code == 200
    content = html.unescape(response.content.decode("utf-8"))
    assert (
        f"Les informations affichées sont basées sur l'exercice comptable {date_cloture_exercice.year}."
        in content
    ), content


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
