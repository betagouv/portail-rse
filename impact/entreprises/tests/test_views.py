import html
from datetime import date

import pytest
from django.conf import settings
from django.urls import reverse
from freezegun import freeze_time
from pytest_django.asserts import assertTemplateUsed

import api.exceptions
from conftest import CODE_PAYS_PORTUGAL
from entreprises.models import CaracteristiquesAnnuelles
from entreprises.models import Entreprise
from entreprises.views import get_current_entreprise
from habilitations.models import Habilitation


@pytest.mark.django_db()
def test_get_current_entreprise_avec_une_entreprise_en_session(
    client, entreprise_factory
):
    siren = "123456789"
    entreprise = entreprise_factory(siren=siren)
    session = client.session
    session["entreprise"] = siren
    session.save()

    request = client.get("/").wsgi_request

    assert get_current_entreprise(request) == entreprise


@pytest.mark.django_db()
def test_get_current_entreprise_avec_une_entreprise_en_session_mais_inexistante_en_base(
    client,
):
    session = client.session
    session["entreprise"] = "123456789"
    session.save()

    request = client.get(reverse("contact")).wsgi_request

    assert get_current_entreprise(request) is None
    session = client.session
    assert "entreprise" not in session


@pytest.mark.django_db()
def test_get_current_entreprise_sans_entreprise_en_session(client):
    request = client.get("/").wsgi_request

    assert get_current_entreprise(request) is None


def test_get_current_entreprise_avec_utilisateur_rattache_a_une_entreprise(
    client, alice, entreprise_factory
):
    entreprise = entreprise_factory()
    Habilitation.ajouter(entreprise, alice, fonctions="Présidente")
    client.force_login(alice)

    request = client.get("/").wsgi_request

    assert get_current_entreprise(request) == entreprise


def test_get_current_entreprise_avec_utilisateur_rattache_a_plusieurs_entreprise(
    client, alice, entreprise_factory
):
    entreprise1 = entreprise_factory(siren="000000001")
    entreprise2 = entreprise_factory(siren="000000002")
    Habilitation.ajouter(entreprise1, alice, fonctions="Présidente")
    Habilitation.ajouter(entreprise2, alice, fonctions="Présidente")
    client.force_login(alice)

    request = client.get("/").wsgi_request

    assert get_current_entreprise(request) == entreprise1


def test_get_current_entreprise_avec_utilisateur_sans_entreprise(client, alice):
    client.force_login(alice)

    request = client.get("/").wsgi_request

    assert get_current_entreprise(request) is None


def test_search_and_create_entreprise(db, mock_api_infos_entreprise):
    mock_api_infos_entreprise.return_value = {
        "siren": "123456789",
        "denomination": "Entreprise SAS",
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10,
        "categorie_juridique_sirene": 5710,
        "code_pays_etranger_sirene": CODE_PAYS_PORTUGAL,
        "code_NAF": "01.11Z",
    }

    Entreprise.search_and_create_entreprise("123456789")

    entreprise = Entreprise.objects.get(siren="123456789")
    assert entreprise.denomination == "Entreprise SAS"
    assert entreprise.categorie_juridique_sirene == 5710
    assert entreprise.code_pays_etranger_sirene == CODE_PAYS_PORTUGAL
    assert entreprise.code_NAF == "01.11Z"


def _attach_data(siren):
    return {"siren": siren, "fonctions": "Présidente", "action": "attach"}


def test_entreprises_page_requires_login(client):
    response = client.get("/entreprises")

    assert response.status_code == 302


def test_entreprises_page_for_logged_user(client, alice, entreprise_factory):
    entreprise = entreprise_factory(utilisateur=alice)
    client.force_login(alice)

    response = client.get("/entreprises")

    assert response.status_code == 200
    assertTemplateUsed(response, "entreprises/index.html")


def test_create_and_attach_to_entreprise(client, alice, mock_api_infos_entreprise):
    client.force_login(alice)
    data = _attach_data("000000001")

    response = client.post("/entreprises", data=data, follow=True)

    assert response.status_code == 200
    assert response.redirect_chain == [(reverse("entreprises:entreprises"), 302)]

    content = html.unescape(response.content.decode("utf-8"))
    assert "L'entreprise a été ajoutée." in content

    entreprise = Entreprise.objects.get(siren="000000001")

    assert Habilitation.objects.pour(entreprise, alice).fonctions == "Présidente"
    assert Habilitation.objects.pour(entreprise, alice).fonctions == "Présidente"

    assert entreprise.denomination == "Entreprise SAS"
    assert entreprise.categorie_juridique_sirene == 5710
    assert entreprise.code_NAF == "01.11Z"


def test_attach_to_an_existing_entreprise(client, alice, entreprise_factory):
    entreprise = entreprise_factory()
    client.force_login(alice)
    data = _attach_data(entreprise.siren)

    response = client.post("/entreprises", data=data, follow=True)

    assert response.status_code == 200
    assert response.redirect_chain == [(reverse("entreprises:entreprises"), 302)]
    assert entreprise in alice.entreprises
    assert Habilitation.objects.pour(entreprise, alice).fonctions == "Présidente"


def test_fail_to_create_entreprise(client, alice, mock_api_infos_entreprise):
    client.force_login(alice)
    data = _attach_data("unvalid")

    response = client.post("/entreprises", data=data, follow=True)

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    content = html.unescape(response.content.decode("utf-8"))
    assert (
        "Impossible d'ajouter cette entreprise car les données sont incorrectes."
        in content
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
    Habilitation.ajouter(entreprise, alice, fonctions="DG")
    client.force_login(alice)
    data = _attach_data(entreprise.siren)

    response = client.post("/entreprises", data=data, follow=True)

    assert Habilitation.objects.count() == 1
    assert response.status_code == 200
    content = html.unescape(response.content.decode("utf-8"))
    assert (
        "Impossible d'ajouter cette entreprise. Vous y êtes déjà rattaché·e." in content
    )


def test_échec_car_déjà_un_propriétaire_présent_sur_l_entreprise(
    client, alice, bob, entreprise_factory
):
    entreprise = entreprise_factory()
    Habilitation.ajouter(entreprise, alice, fonctions="DG")
    client.force_login(bob)
    data = _attach_data(entreprise.siren)

    response = client.post("/entreprises", data=data, follow=True)

    assert Habilitation.objects.count() == 1
    assert response.status_code == 200
    content = html.unescape(response.content.decode("utf-8"))
    assert (
        "Impossible d'ajouter cette entreprise. Il existe déjà un propriétaire sur cette entreprise. Contactez la personne concernée (a***e@portail-rse.test) ou notre support (contact@portail-rse.beta.gouv.fr)."
        in content
    )


@pytest.mark.parametrize("is_entreprise_in_session", [True, False])
def test_detach_from_an_entreprise(
    is_entreprise_in_session, client, alice, bob, entreprise_factory
):
    entreprise = entreprise_factory()
    # Bob est ajouté car il faut toujours un propriétaire restant
    Habilitation.ajouter(entreprise, bob, fonctions="Vice-président")
    Habilitation.ajouter(entreprise, alice, fonctions="Présidente")
    client.force_login(alice)
    session = client.session
    if is_entreprise_in_session:
        session["entreprise"] = entreprise.siren
        session.save()

    data = {"siren": entreprise.siren, "action": "detach"}

    response = client.post("/entreprises", data=data, follow=True)

    session = client.session
    assert "entreprise" not in session
    assert response.status_code == 200
    assert (reverse("entreprises:entreprises"), 302) in response.redirect_chain
    assert entreprise not in alice.entreprises
    assert not Habilitation.objects.parEntreprise(entreprise).parUtilisateur(alice)
    content = html.unescape(response.content.decode("utf-8"))
    assert (
        f"Votre compte n'est plus rattaché à l'entreprise {entreprise.denomination}"
        in content
    )


def test_fail_to_detach_without_relation_to_an_entreprise(
    client, alice, entreprise_factory
):
    entreprise = entreprise_factory()
    client.force_login(alice)
    data = {"siren": entreprise.siren, "action": "detach"}

    response = client.post("/entreprises", data=data, follow=True)

    assert response.status_code == 200
    assert (reverse("entreprises:entreprises"), 302) in response.redirect_chain


def test_fail_to_detach_to_an_entreprise_which_does_not_exist(client, alice):
    client.force_login(alice)
    data = {"siren": "000000001", "action": "detach"}

    response = client.post("/entreprises", data=data, follow=True)

    assert response.status_code == 200
    assert (reverse("entreprises:entreprises"), 302) in response.redirect_chain


def test_echec_quitter_entreprise_car_dernier_proprietaire(
    client, alice, entreprise_factory
):
    entreprise = entreprise_factory(utilisateur=alice)
    client.force_login(alice)
    data = {"siren": entreprise.siren, "action": "detach"}

    response = client.post("/entreprises", data=data, follow=True)

    assert response.status_code == 200
    assert (reverse("entreprises:entreprises"), 302) in response.redirect_chain
    assert Habilitation.pour(entreprise, alice)


def test_echec_quitter_entreprise_redirige_vers_tableau_de_bord_si_l_utilisateur_en_vient(
    client, alice, entreprise_factory
):
    # On peut quitter une entreprise depuis son tableau de bord. En cas d'échec, on y est redirigé.
    entreprise = entreprise_factory(utilisateur=alice)
    client.force_login(alice)
    data = {"siren": entreprise.siren, "action": "detach"}

    response = client.post(
        "/entreprises",
        data=data,
        follow=True,
        HTTP_REFERER=reverse(
            "reglementations:tableau_de_bord", args=[entreprise.siren]
        ),
    )

    assert response.status_code == 200
    assert (reverse("reglementations:tableau_de_bord"), 302) in response.redirect_chain
    assert Habilitation.pour(entreprise, alice)


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
):
    mock_api_infos_entreprise.return_value = {
        "siren": entreprise_non_qualifiee.siren,
        "denomination": "Entreprise SAS",
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        "categorie_juridique_sirene": 5710,
        "code_pays_etranger_sirene": CODE_PAYS_PORTUGAL,
        "code_NAF": "01.11Z",
        "date_cloture_exercice": date(2023, 6, 30),
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
        "tranche_chiffre_affaires_consolide": CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
    }

    Habilitation.ajouter(entreprise_non_qualifiee, alice, fonctions="Présidente")
    client.force_login(alice)

    response = client.get(f"/entreprises/{entreprise_non_qualifiee.siren}")

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "<!-- page qualification entreprise -->" in content
    mock_api_infos_entreprise.assert_called_once_with(
        entreprise_non_qualifiee.siren, donnees_financieres=True
    )
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
):
    Habilitation.ajouter(entreprise_non_qualifiee, alice, fonctions="Présidente")
    client.force_login(alice)

    mock_api_infos_entreprise.side_effect = api.exceptions.APIError("yolo")

    with freeze_time(date(2023, 1, 27)):
        response = client.get(f"/entreprises/{entreprise_non_qualifiee.siren}")

    assert response.status_code == 200
    response.content.decode("utf-8")

    context = response.context
    assert context["form"]["date_cloture_exercice"].initial == "2022-12-31"
    assert context["form"]["effectif"].initial is None


def test_page_de_qualification_avec_entreprise_qualifiee_initialise_les_champs_sans_appel_api(
    client,
    alice,
    entreprise_factory,
    mock_api_infos_entreprise,
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
        effectif_securite_sociale=CaracteristiquesAnnuelles.EFFECTIF_SECURITE_SOCIALE_ENTRE_50_ET_249,
        effectif_outre_mer=CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_MOINS_DE_250,
        effectif_groupe=CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        effectif_groupe_france=CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        tranche_chiffre_affaires=CaracteristiquesAnnuelles.CA_MOINS_DE_900K,
        tranche_bilan=CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K,
        tranche_chiffre_affaires_consolide=CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
        tranche_bilan_consolide=CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        bdese_accord=True,
        systeme_management_energie=True,
    )
    Habilitation.ajouter(entreprise, alice, fonctions="Présidente")
    client.force_login(alice)

    with freeze_time(date(2023, 1, 27)):
        response = client.get(f"/entreprises/{entreprise.siren}")

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "<!-- page qualification entreprise -->" in content
    mock_api_infos_entreprise.assert_not_called()
    context = response.context

    form = context["form"]

    # sqlite automatically converts dates to strings,
    # postgres doesn't (datetime).
    assert str(form["date_cloture_exercice"].initial) == "2022-06-30"
    assert form["effectif"].initial == CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10
    assert (
        form["effectif_securite_sociale"].initial
        == CaracteristiquesAnnuelles.EFFECTIF_SECURITE_SOCIALE_ENTRE_50_ET_249
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
):
    entreprise = entreprise_factory()
    Habilitation.ajouter(entreprise, alice, fonctions="Présidente")
    caracs = entreprise.dernieres_caracteristiques_qualifiantes
    caracs.date_cloture_exercice = None
    caracs.save()
    assert not caracs.sont_qualifiantes
    client.force_login(alice)

    with freeze_time(date(2023, 1, 27)):
        response = client.get(f"/entreprises/{entreprise.siren}")

    mock_api_infos_entreprise.assert_not_called()
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
    client, alice, entreprise_non_qualifiee, mock_api_egapro, date_requalification
):
    Habilitation.ajouter(entreprise_non_qualifiee, alice, fonctions="Présidente")

    client.force_login(alice)
    data = {
        "confirmation_naf": "11.11C",
        "date_cloture_exercice": date(2022, 12, 31),
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "effectif_securite_sociale": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "effectif_outre_mer": CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_MOINS_DE_250,
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_ENTRE_900K_ET_50M,
        "tranche_bilan": CaracteristiquesAnnuelles.BILAN_ENTRE_450K_ET_25M,
        "est_cotee": True,
        "est_interet_public": True,
        "appartient_groupe": True,
        "effectif_groupe": CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        "effectif_groupe_france": CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
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
        caracteristiques.effectif_securite_sociale
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
    Habilitation.ajouter(entreprise_non_qualifiee, alice, fonctions="Présidente")
    client.force_login(alice)
    data = {
        "confirmation_naf": "01.11Z",
        "date_cloture_exercice": date(2022, 12, 31),
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "effectif_securite_sociale": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
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
        caracteristiques.effectif_securite_sociale
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
    Habilitation.ajouter(entreprise_non_qualifiee, alice, fonctions="Présidente")
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
    Habilitation.ajouter(entreprise, alice, fonctions="Présidente")
    client.force_login(alice)
    data = {
        "confirmation_naf": "11.11C",
        "date_cloture_exercice": date_cloture_dernier_exercice.replace(
            year=date_cloture_dernier_exercice.year - 1
        ),
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "effectif_securite_sociale": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "effectif_outre_mer": CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_MOINS_DE_250,
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_ENTRE_900K_ET_50M,
        "tranche_bilan": CaracteristiquesAnnuelles.BILAN_ENTRE_450K_ET_25M,
        "bdese_accord": True,
        "systeme_management_energie": True,
    }

    url = f"/entreprises/{entreprise.siren}"
    client.post(url, data=data)

    assert not entreprise.caracteristiques_annuelles(date_cloture_dernier_exercice.year)
    assert entreprise.caracteristiques_annuelles(date_cloture_dernier_exercice.year - 1)


def test_recherche_entreprise_avec_resultats(
    client, mock_api_recherche_par_nom_ou_siren
):
    nombre_resultats = 3
    entreprises = [
        {"siren": "000000001", "denomination": "Entreprise Test 1"},
        {"siren": "889297453", "denomination": "YAAL COOP"},
        {"siren": "552032534", "denomination": "DANONE"},
    ]
    mock_api_recherche_par_nom_ou_siren.return_value = {
        "nombre_resultats": nombre_resultats,
        "entreprises": entreprises,
    }
    recherche = "Entreprise SAS"

    response = client.get(
        "/entreprises/fragments/recherche-entreprise",
        query_params={"recherche": recherche},
    )

    mock_api_recherche_par_nom_ou_siren.assert_called_once_with(recherche)
    assert response.status_code == 200
    context = response.context
    assert context["nombre_resultats"] == nombre_resultats
    assert context["entreprises"] == entreprises
    assert context["recherche"] == recherche
    assert context["erreur_recherche_entreprise"] is None
    assertTemplateUsed(response, "fragments/resultats_recherche_entreprise.html")
    content = response.content.decode("utf-8")
    assert reverse("entreprises:preremplissage_siren") in content


def test_recherche_entreprise_moins_de_3_caractères(
    client, mock_api_recherche_par_nom_ou_siren
):
    recherche = "En"

    response = client.get(
        "/entreprises/fragments/recherche-entreprise",
        query_params={"recherche": recherche},
    )

    assert not mock_api_recherche_par_nom_ou_siren.called
    assert response.status_code == 200
    context = response.context
    assert context["recherche"] == recherche
    assertTemplateUsed(response, "fragments/resultats_recherche_entreprise.html")


def test_recherche_entreprise_erreur_API(client, mock_api_recherche_par_nom_ou_siren):
    mock_api_recherche_par_nom_ou_siren.side_effect = api.exceptions.APIError(
        "Panne serveur"
    )
    recherche = "Entreprise SAS"

    response = client.get(
        "/entreprises/fragments/recherche-entreprise",
        query_params={"recherche": recherche},
    )

    assert response.status_code == 200
    context = response.context
    assert context["erreur_recherche_entreprise"] == "Panne serveur"
    assertTemplateUsed(response, "fragments/resultats_recherche_entreprise.html")
    content = response.content.decode("utf-8")
    assert "Panne serveur" in content


def test_recherche_entreprise_avec_siren_entreprise_test(
    client, mock_api_recherche_par_nom_ou_siren
):
    recherche = settings.SIREN_ENTREPRISE_TEST

    response = client.get(
        "/entreprises/fragments/recherche-entreprise",
        query_params={"recherche": recherche},
    )

    assert not mock_api_recherche_par_nom_ou_siren.called
    assert response.status_code == 200
    context = response.context
    assert context["nombre_resultats"] == 1
    assert context["entreprises"] == [
        {
            "siren": settings.SIREN_ENTREPRISE_TEST,
            "denomination": "ENTREPRISE TEST",
            "activite": "Cultures non permanentes",
        }
    ]


def test_recherche_entreprise_avec_htmx_fragment_renseigné(
    client, mock_api_recherche_par_nom_ou_siren
):
    siren = "889297453"
    nombre_resultats = 1
    entreprises = [
        {"siren": siren, "denomination": "YAAL COOP"},
    ]
    mock_api_recherche_par_nom_ou_siren.return_value = {
        "nombre_resultats": nombre_resultats,
        "entreprises": entreprises,
    }
    recherche = "Entreprise SAS"
    htmx_fragment_view_name = "preremplissage_formulaire_simulation"

    response = client.get(
        "/entreprises/fragments/recherche-entreprise",
        query_params={
            "recherche": recherche,
            "htmx_fragment_view_name": htmx_fragment_view_name,
        },
    )

    mock_api_recherche_par_nom_ou_siren.assert_called_once_with(recherche)
    assert response.status_code == 200
    context = response.context
    assert context["htmx_fragment_view_name"] == htmx_fragment_view_name
    content = response.content.decode("utf-8")
    assert reverse(htmx_fragment_view_name) in content


def test_recherche_entreprise_sans_parametre_recherche(
    client, mock_api_recherche_par_nom_ou_siren
):
    response = client.get("/entreprises/fragments/recherche-entreprise")

    assert not mock_api_recherche_par_nom_ou_siren.called
    assert response.status_code == 400


def test_preremplissage_siren(client):
    siren = "123456789"
    denomination = "ENTREPRISE"

    response = client.get(
        "/entreprises/fragments/preremplissage-siren",
        query_params={
            "siren": siren,
            "denomination": denomination,
        },
    )

    assert response.status_code == 200
    assertTemplateUsed(response, "fragments/siren_field.html")
    preremplissage_form = response.context["form"]
    assert preremplissage_form["siren"].value() == siren
    assert preremplissage_form["denomination"].value() == denomination


@pytest.mark.django_db
def test_conseiller_rse_ne_peut_pas_modifier_qualification(
    client, entreprise_factory, alice, django_user_model
):
    """Un conseiller RSE (EDITEUR) ne peut pas accéder à la page de qualification."""
    from habilitations.enums import UserRole

    # Créer une entreprise avec un propriétaire
    entreprise = entreprise_factory(siren="123456789")
    Habilitation.ajouter(entreprise, alice, UserRole.PROPRIETAIRE)

    # Créer un conseiller RSE avec rôle EDITEUR
    conseiller = django_user_model.objects.create(
        email="conseiller@test.fr", is_conseiller_rse=True
    )
    Habilitation.ajouter(entreprise, conseiller, UserRole.EDITEUR)

    # Se connecter en tant que conseiller
    client.force_login(conseiller)

    # Essayer d'accéder à la page de qualification
    response = client.get(
        reverse("entreprises:qualification", kwargs={"siren": "123456789"})
    )

    # Vérifier qu'on reçoit une erreur 403
    assert response.status_code == 403
    assertTemplateUsed(response, "403.html")
