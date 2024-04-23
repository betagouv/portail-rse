import html
from datetime import date
from unittest import mock

import pytest
from django.urls import reverse
from freezegun import freeze_time

import api.exceptions
from api.tests.fixtures import mock_api_egapro  # noqa
from api.tests.fixtures import mock_api_infos_entreprise  # noqa
from api.tests.fixtures import mock_api_ratios_financiers  # noqa
from conftest import CODE_PAYS_PORTUGAL
from entreprises.models import CaracteristiquesAnnuelles
from entreprises.models import Entreprise
from entreprises.views import get_current_entreprise
from entreprises.views import search_and_create_entreprise
from habilitations.models import attach_user_to_entreprise
from habilitations.models import get_habilitation
from habilitations.models import Habilitation
from habilitations.models import is_user_attached_to_entreprise


def test_get_current_entreprise_avec_une_entreprise_en_session_mais_inexistante_en_base(
    client, alice
):
    session = client.session
    session["entreprise"] = "123456789"
    session.save()
    request = client.get("/").wsgi_request

    assert get_current_entreprise(request) is None
    session = client.session
    assert "entreprise" not in session


def test_search_and_create_entreprise(db, mock_api_infos_entreprise):
    mock_api_infos_entreprise.return_value = {
        "siren": "123456789",
        "denomination": "Entreprise SAS",
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        "categorie_juridique_sirene": 5710,
        "code_pays_etranger_sirene": CODE_PAYS_PORTUGAL,
    }

    search_and_create_entreprise("123456789")

    entreprise = Entreprise.objects.get(siren="123456789")
    assert entreprise.denomination == "Entreprise SAS"
    assert entreprise.categorie_juridique_sirene == 5710
    assert entreprise.code_pays_etranger_sirene == CODE_PAYS_PORTUGAL


def _attach_data(siren):
    return {"siren": siren, "fonctions": "Présidente", "action": "attach"}


def test_entreprises_page_requires_login(client):
    response = client.get("/entreprises")

    assert response.status_code == 302


def test_entreprises_page_for_logged_user(client, alice, entreprise_factory):
    entreprise = entreprise_factory()
    attach_user_to_entreprise(alice, entreprise, "Présidente")
    client.force_login(alice)

    response = client.get("/entreprises")

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "<!-- page entreprises -->" in content


def test_create_and_attach_to_entreprise(client, alice, mock_api_infos_entreprise):
    client.force_login(alice)
    data = _attach_data("000000001")

    response = client.post("/entreprises", data=data, follow=True)

    assert response.status_code == 200
    assert response.redirect_chain == [(reverse("entreprises:entreprises"), 302)]

    content = html.unescape(response.content.decode("utf-8"))
    assert "L'entreprise a été ajoutée." in content

    entreprise = Entreprise.objects.get(siren="000000001")
    assert get_habilitation(alice, entreprise).fonctions == "Présidente"
    assert entreprise.denomination == "Entreprise SAS"
    assert entreprise.categorie_juridique_sirene == 5710


def test_attach_to_an_existing_entreprise(client, alice, entreprise_factory):
    entreprise = entreprise_factory()
    client.force_login(alice)
    data = _attach_data(entreprise.siren)

    response = client.post("/entreprises", data=data, follow=True)

    assert response.status_code == 200
    assert response.redirect_chain == [(reverse("entreprises:entreprises"), 302)]
    assert entreprise in alice.entreprises
    assert get_habilitation(alice, entreprise).fonctions == "Présidente"


def test_fail_to_create_entreprise(client, alice, mock_api_infos_entreprise):
    client.force_login(alice)
    data = _attach_data("unvalid")

    response = client.post("/entreprises", data=data, follow=True)

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    content = html.unescape(response.content.decode("utf-8"))
    assert (
        "Impossible de créer l'entreprise car les données sont incorrectes." in content
    )
    assert Entreprise.objects.count() == 0
    assert not mock_api_infos_entreprise.called


def test_fail_to_find_entreprise_in_API(client, alice, mock_api_infos_entreprise):
    client.force_login(alice)
    mock_api_infos_entreprise.side_effect = api.exceptions.APIError(
        "L'entreprise n'a pas été trouvée. Vérifiez que le SIREN est correct."
    )
    data = _attach_data("000000001")

    response = client.post("/entreprises", data=data, follow=True)

    assert response.status_code == 200
    content = html.unescape(response.content.decode("utf-8"))
    assert (
        "L'entreprise n'a pas été trouvée. Vérifiez que le SIREN est correct."
        in content
    )
    assert Entreprise.objects.count() == 0


def test_fail_because_already_existing_habilitation(client, alice, entreprise_factory):
    entreprise = entreprise_factory()
    attach_user_to_entreprise(alice, entreprise, "DG")
    client.force_login(alice)
    data = _attach_data(entreprise.siren)

    response = client.post("/entreprises", data=data, follow=True)

    assert Habilitation.objects.count() == 1
    assert response.status_code == 200
    content = html.unescape(response.content.decode("utf-8"))
    assert (
        "Impossible d'ajouter cette entreprise. Vous y êtes déjà rattaché·e." in content
    )


@pytest.mark.parametrize("is_entreprise_in_session", [True, False])
def test_detach_from_an_entreprise(
    is_entreprise_in_session, client, alice, entreprise_factory
):
    entreprise = entreprise_factory()
    attach_user_to_entreprise(alice, entreprise, "Présidente")
    client.force_login(alice)
    session = client.session
    if is_entreprise_in_session:
        session["entreprise"] = entreprise.siren
        session.save()

    data = {"siren": entreprise.siren, "action": "detach"}

    response = client.post(f"/entreprises", data=data, follow=True)

    session = client.session
    assert "entreprise" not in session
    assert response.status_code == 200
    assert response.redirect_chain == [(reverse("entreprises:entreprises"), 302)]
    assert entreprise not in alice.entreprises
    assert not is_user_attached_to_entreprise(alice, entreprise)
    content = html.unescape(response.content.decode("utf-8"))
    assert (
        f"Votre compte n'êtes plus rattaché à l'entreprise {entreprise.denomination}"
        in content
    )


def test_fail_to_detach_without_relation_to_an_entreprise(
    client, alice, entreprise_factory
):
    entreprise = entreprise_factory()
    client.force_login(alice)
    data = {"siren": entreprise.siren, "action": "detach"}

    response = client.post(f"/entreprises", data=data, follow=True)

    assert response.status_code == 200
    assert response.redirect_chain == [(reverse("entreprises:entreprises"), 302)]


def test_fail_to_detach_to_an_entreprise_which_does_not_exist(client, alice):
    client.force_login(alice)
    data = {"siren": "000000001", "action": "detach"}

    response = client.post(f"/entreprises", data=data, follow=True)

    assert response.status_code == 200
    assert response.redirect_chain == [(reverse("entreprises:entreprises"), 302)]


def test_qualification_page_is_not_public(client, alice, entreprise_non_qualifiee):
    url = f"/entreprises/{entreprise_non_qualifiee.siren}"
    response = client.get(url)

    assert response.status_code == 302
    connexion_url = reverse("users:login")
    assert response.url == f"{connexion_url}?next={url}"

    client.force_login(alice)
    response = client.get(url)

    assert response.status_code == 403


def test_page_de_qualification_d_une_entreprise_non_qualifiee_pre_remplit_les_champs_par_api(
    client,
    alice,
    entreprise_non_qualifiee,
    mock_api_infos_entreprise,
    mock_api_ratios_financiers,
):
    mock_api_infos_entreprise.return_value = {
        "siren": entreprise_non_qualifiee.siren,
        "denomination": "Entreprise SAS",
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        "categorie_juridique_sirene": 5710,
        "code_pays_etranger_sirene": CODE_PAYS_PORTUGAL,
    }
    mock_api_ratios_financiers.return_value = {
        "date_cloture_exercice": date(2023, 6, 30),
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
        "tranche_chiffre_affaires_consolide": CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    }

    attach_user_to_entreprise(alice, entreprise_non_qualifiee, "Présidente")
    client.force_login(alice)

    response = client.get(f"/entreprises/{entreprise_non_qualifiee.siren}")

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "<!-- page qualification entreprise -->" in content
    mock_api_infos_entreprise.assert_called_once_with(entreprise_non_qualifiee.siren)
    mock_api_ratios_financiers.assert_called_once_with(entreprise_non_qualifiee.siren)
    context = response.context
    # Les champs dont les infos sont récupérées par API sont pré-remplies
    assert context["form"]["date_cloture_exercice"].initial == "2023-06-30"
    assert (
        context["form"]["effectif"].initial
        == CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS
    )
    assert (
        context["form"]["tranche_chiffre_affaires"].initial
        == CaracteristiquesAnnuelles.CA_100M_ET_PLUS
    )
    assert context["form"]["appartient_groupe"].initial
    assert context["form"]["comptes_consolides"].initial
    assert (
        context["form"]["tranche_chiffre_affaires_consolide"].initial
        == CaracteristiquesAnnuelles.CA_100M_ET_PLUS
    )

    # Les autres champs restent vides
    assert not context["form"]["est_societe_mere"].initial
    assert context["form"]["effectif_outre_mer"].initial is None
    assert context["form"]["effectif_groupe"].initial is None
    assert context["form"]["effectif_groupe_france"].initial is None


def test_page_de_qualification_d_une_entreprise_non_qualifiee_avec_erreur_api_non_bloquante(
    client,
    alice,
    entreprise_non_qualifiee,
    mock_api_infos_entreprise,
    mock_api_ratios_financiers,
):
    attach_user_to_entreprise(alice, entreprise_non_qualifiee, "Présidente")
    client.force_login(alice)

    mock_api_infos_entreprise.side_effect = api.exceptions.APIError("yolo")

    with freeze_time(date(2023, 1, 27)):
        response = client.get(f"/entreprises/{entreprise_non_qualifiee.siren}")

    assert response.status_code == 200
    content = response.content.decode("utf-8")

    context = response.context
    assert context["form"]["date_cloture_exercice"].initial == "2022-12-31"
    assert context["form"]["effectif"].initial is None


def test_page_de_qualification_avec_entreprise_qualifiee_initialise_les_champs_sans_appel_api(
    client,
    alice,
    entreprise_factory,
    mock_api_infos_entreprise,
    mock_api_ratios_financiers,
):
    entreprise = entreprise_factory(
        date_cloture_exercice=date(2022, 6, 30),
        appartient_groupe=True,
        est_societe_mere=True,
        societe_mere_en_france=True,
        comptes_consolides=True,
        est_cotee=True,
        est_interet_public=True,
        effectif=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        effectif_outre_mer=CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_MOINS_DE_250,
        effectif_permanent=CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        effectif_groupe=CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        effectif_groupe_france=CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        effectif_groupe_permanent=CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
        tranche_chiffre_affaires_consolide=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
        tranche_bilan_consolide=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        bdese_accord=True,
        systeme_management_energie=True,
    )
    attach_user_to_entreprise(alice, entreprise, "Présidente")
    client.force_login(alice)

    with freeze_time(date(2023, 1, 27)):
        response = client.get(f"/entreprises/{entreprise.siren}")

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "<!-- page qualification entreprise -->" in content
    mock_api_infos_entreprise.assert_not_called()
    mock_api_ratios_financiers.assert_not_called()
    context = response.context

    form = context["form"]
    assert form["date_cloture_exercice"].initial == "2022-06-30"
    assert form["effectif"].initial == CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10
    assert (
        form["effectif_permanent"].initial
        == CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10
    )
    assert (
        form["tranche_chiffre_affaires"].initial
        == CaracteristiquesAnnuelles.CA_MOINS_DE_900K
    )
    assert (
        form["tranche_bilan"].initial == CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K
    )
    assert form["est_cotee"].initial
    assert form["est_interet_public"].initial
    assert form["appartient_groupe"].initial
    assert (
        form["effectif_groupe"].initial
        == CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS
    )
    assert (
        form["effectif_groupe_france"].initial
        == CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS
    )
    assert (
        form["effectif_groupe_permanent"].initial
        == CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999
    )
    assert form["est_societe_mere"].initial
    assert form["societe_mere_en_france"].initial
    assert form["comptes_consolides"].initial
    assert (
        form["tranche_chiffre_affaires_consolide"].initial
        == CaracteristiquesAnnuelles.CA_100M_ET_PLUS
    )
    assert (
        form["tranche_bilan_consolide"].initial
        == CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS
    )
    assert form["bdese_accord"].initial
    assert form["systeme_management_energie"].initial


def test_page_de_qualification_avec_des_caracteristiques_non_qualifiantes_initialise_les_champs_sans_appel_api(
    client,
    alice,
    entreprise_factory,
    mock_api_infos_entreprise,
    mock_api_ratios_financiers,
):
    entreprise = entreprise_factory()
    attach_user_to_entreprise(alice, entreprise, "Présidente")
    caracs = entreprise.dernieres_caracteristiques_qualifiantes
    caracs.date_cloture_exercice = None
    caracs.save()
    assert not caracs.sont_qualifiantes
    client.force_login(alice)

    with freeze_time(date(2023, 1, 27)):
        response = client.get(f"/entreprises/{entreprise.siren}")

    mock_api_infos_entreprise.assert_not_called()
    mock_api_ratios_financiers.assert_not_called()
    context = response.context

    form = context["form"]
    assert form["date_cloture_exercice"].initial == "2022-12-31"
    assert form["effectif"].initial == caracs.effectif
    assert form["tranche_chiffre_affaires"].initial == caracs.tranche_chiffre_affaires
    assert form["tranche_bilan"].initial == caracs.tranche_bilan
    assert form["est_cotee"].initial == entreprise.est_cotee
    assert form["est_interet_public"].initial == entreprise.est_interet_public
    assert form["appartient_groupe"].initial == entreprise.appartient_groupe
    assert form["effectif_groupe"].initial == caracs.effectif_groupe
    assert form["effectif_groupe_france"].initial == caracs.effectif_groupe_france
    assert form["est_societe_mere"].initial == entreprise.societe_mere_en_france
    assert form["societe_mere_en_france"].initial == entreprise.societe_mere_en_france
    assert form["comptes_consolides"].initial == entreprise.comptes_consolides
    assert (
        form["tranche_chiffre_affaires_consolide"].initial
        == caracs.tranche_chiffre_affaires_consolide
    )
    assert form["tranche_bilan_consolide"].initial == caracs.tranche_bilan_consolide
    assert form["bdese_accord"].initial == caracs.bdese_accord
    assert (
        form["systeme_management_energie"].initial == caracs.systeme_management_energie
    )


def test_qualifie_entreprise_appartenant_a_un_groupe(
    client,
    alice,
    entreprise_non_qualifiee,
    mock_api_egapro,
):
    attach_user_to_entreprise(alice, entreprise_non_qualifiee, "Présidente")
    client.force_login(alice)
    data = {
        "date_cloture_exercice": date(2022, 12, 31),
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "effectif_permanent": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "effectif_outre_mer": CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_MOINS_DE_250,
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_ENTRE_900K_ET_50M,
        "tranche_bilan": CaracteristiquesAnnuelles.BILAN_ENTRE_450K_ET_25M,
        "est_cotee": True,
        "est_interet_public": True,
        "appartient_groupe": True,
        "effectif_groupe": CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        "effectif_groupe_france": CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        "effectif_groupe_permanent": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
        "est_societe_mere": True,
        "societe_mere_en_france": True,
        "comptes_consolides": True,
        "tranche_chiffre_affaires_consolide": CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
        "tranche_bilan_consolide": CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        "bdese_accord": True,
        "systeme_management_energie": True,
    }

    with freeze_time(date(2023, 10, 25)):
        url = f"/entreprises/{entreprise_non_qualifiee.siren}"
        response = client.post(url, data=data, follow=True)

    assert response.status_code == 200
    assert response.redirect_chain == [
        (
            reverse(
                "reglementations:tableau_de_bord", args=[entreprise_non_qualifiee.siren]
            ),
            302,
        )
    ]
    content = html.unescape(response.content.decode("utf-8"))
    assert "Les informations de l'entreprise ont été mises à jour." in content

    entreprise_non_qualifiee.refresh_from_db()
    assert entreprise_non_qualifiee.date_derniere_qualification == date(2023, 10, 25)
    assert entreprise_non_qualifiee.denomination == "Entreprise SAS"
    assert entreprise_non_qualifiee.date_cloture_exercice == date(2022, 12, 31)
    assert entreprise_non_qualifiee.est_cotee
    assert entreprise_non_qualifiee.est_interet_public
    assert entreprise_non_qualifiee.appartient_groupe
    assert entreprise_non_qualifiee.est_societe_mere
    assert entreprise_non_qualifiee.societe_mere_en_france
    assert entreprise_non_qualifiee.comptes_consolides
    caracteristiques = entreprise_non_qualifiee.caracteristiques_annuelles(2022)
    assert (
        caracteristiques.effectif == CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249
    )
    assert (
        caracteristiques.effectif_permanent
        == CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249
    )
    assert (
        caracteristiques.effectif_outre_mer
        == CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_MOINS_DE_250
    )
    assert (
        caracteristiques.effectif_groupe
        == CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS
    )
    assert (
        caracteristiques.effectif_groupe_permanent
        == CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999
    )
    assert (
        caracteristiques.effectif_groupe_france
        == CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS
    )
    assert (
        caracteristiques.tranche_chiffre_affaires
        == CaracteristiquesAnnuelles.CA_ENTRE_900K_ET_50M
    )
    assert (
        caracteristiques.tranche_bilan
        == CaracteristiquesAnnuelles.BILAN_ENTRE_450K_ET_25M
    )
    assert (
        caracteristiques.tranche_chiffre_affaires_consolide
        == CaracteristiquesAnnuelles.CA_100M_ET_PLUS
    )
    assert (
        caracteristiques.tranche_bilan_consolide
        == CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS
    )
    assert caracteristiques.bdese_accord
    assert caracteristiques.systeme_management_energie
    assert caracteristiques.sont_qualifiantes


def test_qualifie_entreprise_sans_groupe(
    client,
    alice,
    entreprise_non_qualifiee,
    mock_api_egapro,
):
    attach_user_to_entreprise(alice, entreprise_non_qualifiee, "Présidente")
    client.force_login(alice)
    data = {
        "date_cloture_exercice": date(2022, 12, 31),
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "effectif_permanent": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "effectif_outre_mer": CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_MOINS_DE_250,
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_ENTRE_900K_ET_50M,
        "tranche_bilan": CaracteristiquesAnnuelles.BILAN_ENTRE_450K_ET_25M,
        "est_cotee": True,
        "est_interet_public": True,
        "bdese_accord": True,
        "systeme_management_energie": True,
    }

    url = f"/entreprises/{entreprise_non_qualifiee.siren}"
    response = client.post(url, data=data)

    assert response.status_code == 302

    entreprise_non_qualifiee.refresh_from_db()
    assert entreprise_non_qualifiee.denomination == "Entreprise SAS"
    assert entreprise_non_qualifiee.date_cloture_exercice == date(2022, 12, 31)
    assert entreprise_non_qualifiee.est_cotee
    assert entreprise_non_qualifiee.est_interet_public
    assert entreprise_non_qualifiee.appartient_groupe is False
    assert entreprise_non_qualifiee.est_societe_mere is None
    assert entreprise_non_qualifiee.societe_mere_en_france is None
    assert entreprise_non_qualifiee.comptes_consolides is None
    caracteristiques = entreprise_non_qualifiee.caracteristiques_annuelles(2022)
    assert (
        caracteristiques.effectif == CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249
    )
    assert (
        caracteristiques.effectif_permanent
        == CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249
    )
    assert (
        caracteristiques.effectif_outre_mer
        == CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_MOINS_DE_250
    )
    assert caracteristiques.effectif_groupe is None
    assert caracteristiques.effectif_groupe_france is None
    assert (
        caracteristiques.tranche_chiffre_affaires
        == CaracteristiquesAnnuelles.CA_ENTRE_900K_ET_50M
    )
    assert (
        caracteristiques.tranche_bilan
        == CaracteristiquesAnnuelles.BILAN_ENTRE_450K_ET_25M
    )
    assert caracteristiques.tranche_chiffre_affaires_consolide is None
    assert caracteristiques.tranche_bilan_consolide is None
    assert caracteristiques.bdese_accord
    assert caracteristiques.systeme_management_energie
    assert caracteristiques.sont_qualifiantes


def test_echoue_a_qualifier_l_entreprise(client, alice, entreprise_non_qualifiee):
    attach_user_to_entreprise(alice, entreprise_non_qualifiee, "Présidente")
    client.force_login(alice)
    data = {
        "effectif": "yolo",
        "bdese_accord": True,
    }

    url = f"/entreprises/{entreprise_non_qualifiee.siren}"
    response = client.post(url, data=data)

    assert response.status_code == 200
    content = html.unescape(response.content.decode("utf-8"))
    assert (
        "Les informations de l'entreprise n'ont pas été mises à jour car le formulaire contient des erreurs."
        in content
    )

    entreprise_non_qualifiee.refresh_from_db()
    assert not entreprise_non_qualifiee.dernieres_caracteristiques_qualifiantes


def test_qualification_supprime_les_caracteristiques_annuelles_posterieures_a_la_date_de_cloture_du_dernier_exercice(
    client,
    alice,
    entreprise_factory,
    date_cloture_dernier_exercice,
    mock_api_infos_entreprise,
):
    """Cas limite
    Ce cas pourrait exister si un utilisateur corrige la date de clôture du dernier exercice en la reculant dans le passé.
    """
    entreprise = entreprise_factory()
    assert entreprise.caracteristiques_annuelles(date_cloture_dernier_exercice.year)
    assert not entreprise.caracteristiques_annuelles(
        date_cloture_dernier_exercice.year - 1
    )
    attach_user_to_entreprise(alice, entreprise, "Présidente")
    client.force_login(alice)
    data = {
        "date_cloture_exercice": date_cloture_dernier_exercice.replace(
            year=date_cloture_dernier_exercice.year - 1
        ),
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "effectif_permanent": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "effectif_outre_mer": CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_MOINS_DE_250,
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_ENTRE_900K_ET_50M,
        "tranche_bilan": CaracteristiquesAnnuelles.BILAN_ENTRE_450K_ET_25M,
        "bdese_accord": True,
        "systeme_management_energie": True,
    }

    url = f"/entreprises/{entreprise.siren}"
    response = client.post(url, data=data)

    assert not entreprise.caracteristiques_annuelles(date_cloture_dernier_exercice.year)
    assert entreprise.caracteristiques_annuelles(date_cloture_dernier_exercice.year - 1)


def test_succes_api_search_entreprise(
    client, mock_api_infos_entreprise, mock_api_ratios_financiers
):
    siren = "123456789"
    mock_api_infos_entreprise.return_value = {
        "siren": siren,
        "denomination": "Entreprise SAS",
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        "categorie_juridique_sirene": 5710,
        "code_pays_etranger_sirene": CODE_PAYS_PORTUGAL,
    }
    mock_api_ratios_financiers.return_value = {
        "date_cloture_exercice": date(2023, 12, 31),
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
        "tranche_chiffre_affaires_consolide": CaracteristiquesAnnuelles.CA_MOINS_DE_60M,
    }

    response = client.get(f"/api/search-entreprise/{siren}")

    mock_api_infos_entreprise.assert_called_once_with(siren)
    mock_api_ratios_financiers.assert_called_once_with(siren)
    assert response.status_code == 200
    assert response.json() == {
        "siren": siren,
        "denomination": "Entreprise SAS",
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        "categorie_juridique_sirene": 5710,
        "code_pays_etranger_sirene": CODE_PAYS_PORTUGAL,
        "date_cloture_exercice": "2023-12-31",
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
        "tranche_chiffre_affaires_consolide": CaracteristiquesAnnuelles.CA_MOINS_DE_60M,
    }


def test_echec_api_search_entreprise_car_l_API_infos_entreprise_est_en_erreur(
    client, mock_api_infos_entreprise
):
    mock_api_infos_entreprise.side_effect = api.exceptions.APIError("Panne serveur")

    response = client.get("/api/search-entreprise/123456789")

    assert response.status_code == 400
    assert response.json() == {
        "error": "Panne serveur",
    }


def test_succes_api_search_entreprise_car_l_API_ratios_financiers_n_est_pas_bloquante_même_si_en_erreur(
    client, mock_api_infos_entreprise, mock_api_ratios_financiers
):
    mock_api_ratios_financiers.side_effect = api.exceptions.APIError("Panne serveur")

    response = client.get("/api/search-entreprise/123456789")

    assert response.status_code == 200
    assert response.json() == {
        "siren": mock.ANY,
        "denomination": mock.ANY,
        "effectif": mock.ANY,
        "categorie_juridique_sirene": mock.ANY,
        "code_pays_etranger_sirene": mock.ANY,
        "date_cloture_exercice": None,
        "tranche_chiffre_affaires": None,
        "tranche_chiffre_affaires_consolide": None,
    }
