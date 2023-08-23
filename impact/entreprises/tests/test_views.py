import html
from datetime import date

import pytest
from django.urls import reverse
from freezegun import freeze_time

import api.exceptions
from api.tests.fixtures import mock_api_index_egapro  # noqa
from api.tests.fixtures import mock_api_recherche_entreprises  # noqa
from entreprises.models import CaracteristiquesAnnuelles
from entreprises.models import Entreprise
from entreprises.views import get_current_entreprise
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


def test_create_and_attach_to_entreprise(client, alice, mock_api_recherche_entreprises):
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


def test_attach_to_an_existing_entreprise(client, alice, entreprise_factory):
    entreprise = entreprise_factory()
    client.force_login(alice)
    data = _attach_data(entreprise.siren)

    response = client.post("/entreprises", data=data, follow=True)

    assert response.status_code == 200
    assert response.redirect_chain == [(reverse("entreprises:entreprises"), 302)]
    assert entreprise in alice.entreprises
    assert get_habilitation(alice, entreprise).fonctions == "Présidente"


def test_fail_to_create_entreprise(client, alice):
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


def test_fail_to_find_entreprise_in_API(client, alice, mock_api_recherche_entreprises):
    client.force_login(alice)
    mock_api_recherche_entreprises.side_effect = api.exceptions.APIError(
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


def test_fail_to_detach_whithout_relation_to_an_entreprise(
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


def test_qualification_page_without_current_qualification(
    client, alice, entreprise_non_qualifiee, mock_api_recherche_entreprises
):
    attach_user_to_entreprise(alice, entreprise_non_qualifiee, "Présidente")
    client.force_login(alice)

    with freeze_time(date(2023, 1, 27)):
        response = client.get(f"/entreprises/{entreprise_non_qualifiee.siren}")

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "<!-- page qualification entreprise -->" in content
    mock_api_recherche_entreprises.assert_called_once_with(
        entreprise_non_qualifiee.siren
    )
    context = response.context
    assert context["form"]["date_cloture_exercice"].initial == "2022-12-31"
    assert context["form"]["effectif_outre_mer"].initial is None


def test_qualification_page_with_current_qualification(
    client, alice, entreprise_factory, mock_api_recherche_entreprises
):
    entreprise = entreprise_factory()
    attach_user_to_entreprise(alice, entreprise, "Présidente")
    caracs = entreprise.dernieres_caracteristiques_qualifiantes
    caracs.date_cloture_exercice = date(2022, 6, 30)
    caracs.tranche_chiffre_affaires_consolide = (
        CaracteristiquesAnnuelles.CA_ENTRE_700K_ET_12M
    )
    caracs.tranche_bilan_consolide = CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS
    caracs.save()
    client.force_login(alice)

    with freeze_time(date(2023, 1, 27)):
        response = client.get(f"/entreprises/{entreprise.siren}")

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "<!-- page qualification entreprise -->" in content
    mock_api_recherche_entreprises.assert_not_called()
    context = response.context
    caracs = entreprise.dernieres_caracteristiques_qualifiantes

    assert context["form"]["effectif"].initial == caracs.effectif
    assert (
        context["form"]["tranche_chiffre_affaires"].initial
        == caracs.tranche_chiffre_affaires
    )
    assert context["form"]["tranche_bilan"].initial == caracs.tranche_bilan
    assert context["form"]["appartient_groupe"].initial == entreprise.appartient_groupe
    assert (
        context["form"]["comptes_consolides"].initial == entreprise.comptes_consolides
    )

    assert (
        context["form"]["tranche_chiffre_affaires_consolide"].initial
        == caracs.tranche_chiffre_affaires_consolide
    )
    assert (
        context["form"]["tranche_bilan_consolide"].initial
        == caracs.tranche_bilan_consolide
    )
    assert context["form"]["bdese_accord"].initial == caracs.bdese_accord
    assert (
        context["form"]["systeme_management_energie"].initial
        == caracs.systeme_management_energie
    )
    assert context["form"]["date_cloture_exercice"].initial == "2022-06-30"


def test_qualifie_entreprise_appartenant_a_un_groupe(
    client,
    alice,
    entreprise_non_qualifiee,
    mock_api_recherche_entreprises,
    mock_api_index_egapro,
):
    attach_user_to_entreprise(alice, entreprise_non_qualifiee, "Présidente")
    client.force_login(alice)
    data = {
        "date_cloture_exercice": date(2022, 12, 31),
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "effectif_outre_mer": CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_MOINS_DE_250,
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_ENTRE_700K_ET_12M,
        "tranche_bilan": CaracteristiquesAnnuelles.BILAN_ENTRE_6M_ET_20M,
        "appartient_groupe": True,
        "comptes_consolides": True,
        "tranche_chiffre_affaires_consolide": CaracteristiquesAnnuelles.CA_ENTRE_700K_ET_12M,
        "tranche_bilan_consolide": CaracteristiquesAnnuelles.BILAN_ENTRE_6M_ET_20M,
        "bdese_accord": True,
        "systeme_management_energie": True,
    }

    url = f"/entreprises/{entreprise_non_qualifiee.siren}"
    response = client.get(url)
    response = client.post(url, data=data, follow=True)

    assert response.status_code == 200
    assert response.redirect_chain == [
        (
            reverse(
                "reglementations:reglementations", args=[entreprise_non_qualifiee.siren]
            ),
            302,
        )
    ]
    content = html.unescape(response.content.decode("utf-8"))
    assert "Les caractéristiques de l'entreprise ont été mises à jour." in content

    entreprise_non_qualifiee.refresh_from_db()
    assert entreprise_non_qualifiee.denomination == "Entreprise SAS"
    assert entreprise_non_qualifiee.date_cloture_exercice == date(2022, 12, 31)
    assert entreprise_non_qualifiee.appartient_groupe is True
    assert entreprise_non_qualifiee.comptes_consolides is True
    caracteristiques = entreprise_non_qualifiee.caracteristiques_actuelles()
    assert (
        caracteristiques.effectif == CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249
    )
    assert (
        caracteristiques.effectif_outre_mer
        == CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_MOINS_DE_250
    )
    assert (
        caracteristiques.tranche_chiffre_affaires
        == CaracteristiquesAnnuelles.CA_ENTRE_700K_ET_12M
    )
    assert (
        caracteristiques.tranche_bilan
        == CaracteristiquesAnnuelles.BILAN_ENTRE_6M_ET_20M
    )
    assert (
        caracteristiques.tranche_chiffre_affaires_consolide
        == CaracteristiquesAnnuelles.CA_ENTRE_700K_ET_12M
    )
    assert (
        caracteristiques.tranche_bilan_consolide
        == CaracteristiquesAnnuelles.BILAN_ENTRE_6M_ET_20M
    )
    assert caracteristiques.bdese_accord
    assert caracteristiques.systeme_management_energie


def test_qualifie_entreprise_sans_groupe(
    client,
    alice,
    entreprise_non_qualifiee,
    mock_api_recherche_entreprises,
    mock_api_index_egapro,
):
    attach_user_to_entreprise(alice, entreprise_non_qualifiee, "Présidente")
    client.force_login(alice)
    data = {
        "date_cloture_exercice": date(2022, 12, 31),
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "effectif_outre_mer": CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_MOINS_DE_250,
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_ENTRE_700K_ET_12M,
        "tranche_bilan": CaracteristiquesAnnuelles.BILAN_ENTRE_6M_ET_20M,
        "bdese_accord": True,
        "systeme_management_energie": True,
    }

    url = f"/entreprises/{entreprise_non_qualifiee.siren}"
    response = client.post(url, data=data)

    assert response.status_code == 302

    entreprise_non_qualifiee.refresh_from_db()
    assert entreprise_non_qualifiee.denomination == "Entreprise SAS"
    assert entreprise_non_qualifiee.date_cloture_exercice == date(2022, 12, 31)
    assert entreprise_non_qualifiee.appartient_groupe is False
    assert entreprise_non_qualifiee.comptes_consolides is False
    caracteristiques = entreprise_non_qualifiee.caracteristiques_actuelles()
    assert (
        caracteristiques.effectif == CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249
    )
    assert (
        caracteristiques.tranche_chiffre_affaires
        == CaracteristiquesAnnuelles.CA_ENTRE_700K_ET_12M
    )
    assert (
        caracteristiques.tranche_bilan
        == CaracteristiquesAnnuelles.BILAN_ENTRE_6M_ET_20M
    )
    assert caracteristiques.tranche_chiffre_affaires_consolide is None
    assert caracteristiques.tranche_bilan_consolide is None
    assert caracteristiques.bdese_accord
    assert caracteristiques.systeme_management_energie


def test_qualify_entreprise_error(
    client, alice, entreprise_non_qualifiee, mock_api_recherche_entreprises
):
    attach_user_to_entreprise(alice, entreprise_non_qualifiee, "Présidente")
    client.force_login(alice)
    data = {
        "effectif": "yolo",
        "bdese_accord": True,
    }

    url = f"/entreprises/{entreprise_non_qualifiee.siren}"
    response = client.get(url)
    response = client.post(url, data=data)

    assert response.status_code == 200
    content = html.unescape(response.content.decode("utf-8"))
    assert (
        "Les caractéristiques de l'entreprise n'ont pas été mises à jour car le formulaire contient des erreurs."
        in content
    )

    entreprise_non_qualifiee.refresh_from_db()
    assert not entreprise_non_qualifiee.dernieres_caracteristiques_qualifiantes


@pytest.mark.parametrize(
    "donnees_consolidees",
    [
        {"tranche_bilan_consolide": CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS},
        {
            "tranche_chiffre_affaires_consolide": CaracteristiquesAnnuelles.CA_100M_ET_PLUS
        },
    ],
)
def test_qualification_entreprise_en_erreur_car_comptes_consolides_sans_bilan_ou_ca_consolide(
    donnees_consolidees,
    client,
    alice,
    entreprise_non_qualifiee,
    mock_api_recherche_entreprises,
):
    attach_user_to_entreprise(alice, entreprise_non_qualifiee, "Présidente")
    client.force_login(alice)
    data = {
        "date_cloture_exercice": date(2022, 12, 31),
        "effectif": CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
        "effectif_outre_mer": CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_MOINS_DE_250,
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_ENTRE_700K_ET_12M,
        "tranche_bilan": CaracteristiquesAnnuelles.BILAN_ENTRE_6M_ET_20M,
        "appartient_groupe": True,
        "comptes_consolides": True,
        "bdese_accord": True,
        "systeme_management_energie": True,
    }
    data.update(donnees_consolidees)

    url = f"/entreprises/{entreprise_non_qualifiee.siren}"
    response = client.get(url)
    response = client.post(url, data=data)

    assert response.status_code == 200
    content = html.unescape(response.content.decode("utf-8"))
    assert (
        "Les caractéristiques de l'entreprise n'ont pas été mises à jour car le formulaire contient des erreurs."
        in content
    )
    assert "Ce champ est obligatoire lorsque les comptes sont consolidés" in content

    entreprise_non_qualifiee.refresh_from_db()
    assert not entreprise_non_qualifiee.dernieres_caracteristiques_qualifiantes


def test_qualification_supprime_les_caracteristiques_annuelles_posterieures_a_la_date_de_cloture_du_dernier_exercice(
    client,
    alice,
    entreprise_factory,
    date_cloture_dernier_exercice,
    mock_api_recherche_entreprises,
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
        "effectif_outre_mer": CaracteristiquesAnnuelles.EFFECTIF_OUTRE_MER_MOINS_DE_250,
        "tranche_chiffre_affaires": CaracteristiquesAnnuelles.CA_ENTRE_700K_ET_12M,
        "tranche_bilan": CaracteristiquesAnnuelles.BILAN_ENTRE_6M_ET_20M,
        "bdese_accord": True,
        "systeme_management_energie": True,
    }

    url = f"/entreprises/{entreprise.siren}"
    response = client.post(url, data=data)

    assert not entreprise.caracteristiques_annuelles(date_cloture_dernier_exercice.year)
    assert entreprise.caracteristiques_annuelles(date_cloture_dernier_exercice.year - 1)
