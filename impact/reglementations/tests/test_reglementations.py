import html
from datetime import timedelta

import pytest
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages import WARNING
from django.urls import reverse
from freezegun import freeze_time

from entreprises.models import CaracteristiquesAnnuelles
from habilitations.models import attach_user_to_entreprise
from reglementations.views import REGLEMENTATIONS
from reglementations.views.base import InsuffisammentQualifieeError
from reglementations.views.base import ReglementationStatus


def test_les_reglementations_levent_une_exception_si_les_caracteristiques_sont_vides(
    entreprise_non_qualifiee,
):
    caracteristiques = CaracteristiquesAnnuelles(entreprise=entreprise_non_qualifiee)

    for reglementation in REGLEMENTATIONS:
        with pytest.raises(InsuffisammentQualifieeError):
            reglementation.est_soumis(caracteristiques)
        status = reglementation.calculate_status(caracteristiques, AnonymousUser())
        assert status.status == ReglementationStatus.STATUS_INCALCULABLE


def test_tableau_de_bord_est_prive(client, entreprise_factory, alice):
    entreprise = entreprise_factory()
    url = f"/tableau-de-bord/{entreprise.siren}"

    response = client.get(url)

    assert response.status_code == 302
    connexion_url = reverse("users:login")
    assert response.url == f"{connexion_url}?next={url}"

    client.force_login(alice)
    response = client.get(url)

    assert response.status_code == 403


@pytest.fixture
def entreprise(db, alice, entreprise_factory):
    entreprise = entreprise_factory(
        siren="000000001",
        denomination="Entreprise SAS",
        effectif=CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
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
    reglementations = (
        context["reglementations_a_actualiser"]
        + context["reglementations_en_cours"]
        + context["reglementations_a_jour"]
        + context["reglementations_soumises"]
        + context["reglementations_non_soumises"]
    )
    assert len(reglementations) == len(REGLEMENTATIONS)
    for REGLEMENTATION in REGLEMENTATIONS:
        index = [
            reglementation["reglementation"] for reglementation in reglementations
        ].index(REGLEMENTATION)
        assert reglementations[index]["status"] == REGLEMENTATION.calculate_status(
            entreprise.dernieres_caracteristiques_qualifiantes, entreprise.users.first()
        )
    for reglementation in reglementations:
        assert reglementation["status"].status_detail in content


def test_tableau_de_bord_entreprise_non_qualifiee_redirige_vers_la_qualification(
    client, alice, entreprise_non_qualifiee, mock_api_infos_entreprise
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


def test_tableau_de_bord_sans_siren_redirige_vers_celui_de_l_entreprise_courante(
    client, entreprise, alice
):
    client.force_login(alice)

    url = "/tableau-de-bord"
    response = client.get(url)

    assert response.status_code == 302
    assert response.url == f"/tableau-de-bord/{entreprise.siren}"


def test_tableau_de_bord_sans_siren_et_sans_entreprise(client, alice):
    # Cas limite où un utilisateur n'est rattaché à aucune entreprise
    client.force_login(alice)

    url = "/tableau-de-bord"
    response = client.get(url, follow=True)

    assert response.status_code == 200
    assert response.redirect_chain == [(reverse("entreprises:entreprises"), 302)]
    messages = list(response.context["messages"])
    assert messages[0].level == WARNING
    assert (
        messages[0].message
        == "Commencez par ajouter une entreprise à votre compte utilisateur avant d'accéder à votre tableau de bord"
    )


def test_tableau_de_bord_avec_siren_inexistant(client, alice):
    client.force_login(alice)

    url = "/tableau-de-bord/yolo"
    response = client.get(url)

    assert response.status_code == 404
