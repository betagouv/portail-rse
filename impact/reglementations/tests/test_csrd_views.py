from datetime import datetime

import pytest
from django.contrib.messages import WARNING
from django.urls import reverse

from habilitations.models import attach_user_to_entreprise
from reglementations.models.csrd import Enjeu
from reglementations.models.csrd import RapportCSRD


def test_l_espace_csrd_n_est_pas_publique(client, alice, entreprise_factory):
    entreprise = entreprise_factory()

    url = f"/csrd/{entreprise.siren}"
    response = client.get(url)

    assert response.status_code == 302
    connexion_url = reverse("users:login")
    assert response.url == f"{connexion_url}?next={url}"

    client.force_login(alice)
    response = client.get(url)

    assert response.status_code == 403

    attach_user_to_entreprise(alice, entreprise, "Présidente")
    response = client.get(url)

    assert response.status_code == 200
    assert response.templates[0].name == "reglementations/espace_csrd/index.html"


def test_espace_csrd_sans_siren_redirige_vers_celui_de_l_entreprise_courante(
    client, alice, entreprise_factory
):
    entreprise = entreprise_factory()
    attach_user_to_entreprise(alice, entreprise, "Présidente")
    client.force_login(alice)

    url = "/csrd"
    response = client.get(url)

    assert response.status_code == 302
    assert response.url == f"/csrd/{entreprise.siren}"


def test_espace_csrd_sans_siren_et_sans_entreprise(client, alice):
    # Cas limite où un utilisateur n'est rattaché à aucune entreprise
    client.force_login(alice)

    url = "/csrd"
    response = client.get(url, follow=True)

    assert response.status_code == 200
    assert response.redirect_chain == [(reverse("entreprises:entreprises"), 302)]
    messages = list(response.context["messages"])
    assert messages[0].level == WARNING
    assert (
        messages[0].message
        == "Commencez par ajouter une entreprise à votre compte utilisateur avant d'accéder à l'espace Rapport de Durabilité"
    )


def test_espace_csrd_avec_siren_inexistant(client, alice):
    client.force_login(alice)

    url = "/csrd/yolo"
    response = client.get(url)

    assert response.status_code == 404


@pytest.mark.parametrize(
    "etape",
    [
        "/csrd/{siren}/phase-1",
        "/csrd/{siren}/phase-1/etape-1",
        "/csrd/{siren}/phase-1/etape-1-1",
        "/csrd/{siren}/phase-1/etape-1-1",
        "/csrd/{siren}/phase-1/etape-1-3",
        "/csrd/{siren}/phase-1/etape-2",
        "/csrd/{siren}/phase-1/etape-2-1",
        "/csrd/{siren}/phase-1/etape-2-2",
        "/csrd/{siren}/phase-1/etape-3",
        "/csrd/{siren}/phase-1/etape-3-1",
        "/csrd/{siren}/phase-1/etape-3-2",
        "/csrd/{siren}/phase-1/etape-3-3",
        "/csrd/{siren}/phase-2",
        "/csrd/{siren}/phase-2/etape-1",
        "/csrd/{siren}/phase-3",
        "/csrd/{siren}/phase-3/etape-1",
    ],
)
def test_les_etapes_de_la_csrd(etape, client, alice, entreprise_factory):
    entreprise = entreprise_factory()
    url = etape.format(siren=entreprise.siren)

    response = client.get(url)

    assert response.status_code == 302
    connexion_url = reverse("users:login")
    assert response.url == f"{connexion_url}?next={url}"

    attach_user_to_entreprise(alice, entreprise, "Présidente")
    client.force_login(alice)
    response = client.get(url)

    assert response.status_code == 200
    context = response.context
    assert context["entreprise"] == entreprise
    assert "phase" in context
    assert "etape" in context
    assert "sous_etape" in context

    etape_inexistante = "/csrd/phase-4/etape-1"
    response = client.get(etape_inexistante)

    assert response.status_code == 404

    rapport_csrd = RapportCSRD.objects.get(proprietaire=alice, entreprise=entreprise)
    NOMBRE_ENJEUX = 103
    assert len(rapport_csrd.enjeux.all()) == NOMBRE_ENJEUX


def test_visualisation_des_enjeux(client, alice, entreprise_non_qualifiee):
    attach_user_to_entreprise(alice, entreprise_non_qualifiee, "Présidente")
    csrd = RapportCSRD.objects.create(
        proprietaire=alice,
        entreprise=entreprise_non_qualifiee,
        annee=f"{datetime.now():%Y}",
    )
    client.force_login(alice)

    response = client.get(f"/csrd/fragments/selection_enjeux/{csrd.id}/ESRS_E1", {})

    assert response.status_code == 200
    assert "<!-- fragment enjeux -->" in response.content.decode("utf-8")


def test_selection_et_deselection_d_enjeux(client, alice, entreprise_non_qualifiee):
    attach_user_to_entreprise(alice, entreprise_non_qualifiee, "Présidente")
    csrd = RapportCSRD.objects.create(
        proprietaire=alice,
        entreprise=entreprise_non_qualifiee,
        annee=f"{datetime.now():%Y}",
    )
    enjeux = csrd.enjeux.all()
    enjeu_adaptation = enjeux[0]
    enjeu_attenuation = enjeux[1]
    enjeu_attenuation.selection = True
    enjeu_attenuation.save()
    enjeu_energie = enjeux[2]
    client.force_login(alice)

    response = client.post(
        f"/csrd/fragments/selection_enjeux/{csrd.id}/ESRS_E1",
        {"enjeux": [enjeu_adaptation.id, enjeu_energie.id]},
    )

    enjeu_adaptation.refresh_from_db()
    enjeu_attenuation.refresh_from_db()
    enjeu_energie.refresh_from_db()
    assert [enjeu_adaptation, enjeu_energie] == list(Enjeu.objects.selectionnes())
    assert response.status_code == 200
    context = response.context
    assert context["csrd"] == csrd
    assert "<!-- fragment esrs -->" in response.content.decode("utf-8")
