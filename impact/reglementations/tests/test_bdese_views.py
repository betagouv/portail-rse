import html
import json

from django.urls import reverse
import pytest

from habilitations.models import add_entreprise_to_user
from reglementations.models import annees_a_remplir_bdese, BDESE_50_300, BDESE_300
from reglementations.tests.test_bdese_forms import configuration_form_data
from reglementations.views import get_bdese_data_from_egapro, render_bdese_pdf_html


def test_bdese_is_not_public(client, alice, grande_entreprise):
    url = f"/bdese/{grande_entreprise.siren}/2022/1"
    response = client.get(url)

    assert response.status_code == 302
    connexion_url = reverse("login")
    assert response.url == f"{connexion_url}?next={url}"

    client.force_login(alice)
    response = client.get(url)

    assert response.status_code == 403


@pytest.mark.parametrize(
    "effectif, bdese_class", [("moyen", BDESE_50_300), ("grand", BDESE_300)]
)
def test_yearly_personal_bdese_is_created_at_first_authorized_request(
    effectif, bdese_class, client, alice, entreprise_factory
):
    entreprise = entreprise_factory(effectif=effectif)
    entreprise.users.add(alice)
    client.force_login(alice)

    assert not bdese_class.objects.filter(entreprise=entreprise)

    url = f"/bdese/{entreprise.siren}/2021/1"
    response = client.get(url)

    assert response.status_code == 302
    bdese_2021 = bdese_class.personals.get(entreprise=entreprise, annee=2021)
    assert bdese_2021.user == alice

    url = f"/bdese/{entreprise.siren}/2022/1"
    response = client.get(url)

    bdese_2022 = bdese_class.personals.get(entreprise=entreprise, annee=2022)
    assert bdese_2022.user == alice
    assert bdese_2021 != bdese_2022


def bdese_step_url(bdese, step):
    return f"/bdese/{bdese.entreprise.siren}/{bdese.annee}/{step}"


def test_bdese_step_redirect_to_configuration_if_bdese_not_configured(
    bdese, habilitated_user, client
):
    client.force_login(habilitated_user)

    url = bdese_step_url(bdese, 1)
    response = client.get(url, follow=True)

    assert response.status_code == 200
    assert response.redirect_chain == [
        (
            reverse(
                "bdese",
                args=[bdese.entreprise.siren, bdese.annee, 0],
            ),
            302,
        )
    ]
    assert (
        f"Commencez par configurer votre BDESE {bdese.annee}"
        in response.content.decode("utf-8")
    )


@pytest.fixture
def configured_bdese(bdese):
    bdese.categories_professionnelles = [
        "catégorie 1",
        "catégorie 2",
        "catégorie 3",
    ]
    if bdese.is_bdese_300:
        bdese.categories_professionnelles_detaillees = [
            "catégorie détaillée 1",
            "catégorie détaillée 2",
            "catégorie détaillée 3",
            "catégorie détaillée 4",
            "catégorie détaillée 5",
        ]
        bdese.niveaux_hierarchiques = ["niveau 1", "niveau 2"]
    bdese.mark_step_as_complete(0)
    bdese.save()
    return bdese


def test_check_if_several_users_are_on_the_same_BDESE(
    configured_bdese, habilitated_user, client, bob
):
    bdese = configured_bdese
    add_entreprise_to_user(bdese.entreprise, bob, "Vice-président")
    client.force_login(bob)

    url = bdese_step_url(bdese, 0)
    response = client.get(url)

    assert response.status_code == 200
    content = html.unescape(response.content.decode("utf-8"))
    assert (
        "Plusieurs utilisateurs sont liés à cette entreprise. Les informations que vous remplissez ne sont pas partagés avec les autres utilisateurs tant que vous n'êtes pas habilités."
        in content
    )

    client.force_login(habilitated_user)

    response = client.get(url)

    assert response.status_code == 200
    content = html.unescape(response.content.decode("utf-8"))
    assert (
        "Plusieurs utilisateurs sont liés à cette entreprise. Les informations que vous remplissez ne sont pas partagés avec les autres utilisateurs tant que vous n'êtes pas habilités."
        not in content
    )


def test_bdese_step_use_configured_categories_and_annees_a_remplir(
    configured_bdese, habilitated_user, client
):
    bdese = configured_bdese
    client.force_login(habilitated_user)

    url = bdese_step_url(bdese, 1)
    response = client.get(url)

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    for category in bdese.categories_professionnelles:
        assert category in content
    if bdese.is_bdese_300:
        for category in bdese.categories_professionnelles_detaillees:
            assert category in content
    for annee in annees_a_remplir_bdese():
        assert str(annee) in content

    if bdese.is_bdese_300:
        url = bdese_step_url(
            bdese, 3
        )  # L'étape 3 de la BDESE 300 utilise les niveaux hiérarchiques configurées par l'entreprise
        response = client.get(url)

        content = response.content.decode("utf-8")
        for niveau in bdese.niveaux_hierarchiques:
            assert niveau in content


def test_bdese_step_fetch_data(configured_bdese, habilitated_user, client, mocker):
    bdese = configured_bdese
    client.force_login(habilitated_user)

    fetch_data = mocker.patch("reglementations.views.get_bdese_data_from_egapro")

    url = bdese_step_url(bdese, 1)
    response = client.get(url)

    fetch_data.assert_called_once_with(bdese.entreprise, bdese.annee)


def test_save_step_error(configured_bdese, habilitated_user, client):
    bdese = configured_bdese
    client.force_login(habilitated_user)

    incorrect_data_bdese_300 = {"unite_absenteisme": "yolo"}
    incorrect_data_bdese_50_300 = {"effectif_cdi": "yolo"}
    incorrect_data = (
        incorrect_data_bdese_300 if bdese.is_bdese_300 else incorrect_data_bdese_50_300
    )

    url = bdese_step_url(bdese, 1)
    response = client.post(url, incorrect_data)

    assert response.status_code == 200
    content = html.unescape(response.content.decode("utf-8"))
    assert (
        "L'étape n'a pas été enregistrée car le formulaire contient des erreurs"
        in content
    )

    bdese.refresh_from_db()
    if bdese.is_bdese_300:
        assert bdese.unite_absenteisme != "yolo"
    else:
        assert bdese.effectif_cdi != "yolo"


def test_save_step_as_draft_success(configured_bdese, habilitated_user, client):
    bdese = configured_bdese
    client.force_login(habilitated_user)

    correct_data_bdese_300 = {"unite_absenteisme": "H"}
    correct_data_bdese_50_300 = {"effectif_cdi": "50"}
    correct_data = (
        correct_data_bdese_300 if bdese.is_bdese_300 else correct_data_bdese_50_300
    )

    url = bdese_step_url(bdese, 1)
    response = client.post(url, correct_data, follow=True)

    assert response.status_code == 200
    assert response.redirect_chain == [(url, 302)]

    content = response.content.decode("utf-8")
    assert "Étape enregistrée" in content
    assert "Enregistrer et marquer comme terminé" in content
    assert "Enregistrer en brouillon" in content

    bdese.refresh_from_db()
    if bdese.is_bdese_300:
        assert bdese.unite_absenteisme == "H"
    else:
        assert bdese.effectif_cdi == 50
    assert not bdese.step_is_complete(1)


def test_save_step_and_mark_as_complete_success(
    configured_bdese, habilitated_user, client
):
    bdese = configured_bdese
    client.force_login(habilitated_user)

    correct_data_bdese_300 = {"unite_absenteisme": "H"}
    correct_data_bdese_50_300 = {"effectif_cdi": "50"}
    correct_data = (
        correct_data_bdese_300 if bdese.is_bdese_300 else correct_data_bdese_50_300
    )
    correct_data.update({"save_complete": ""})

    url = bdese_step_url(bdese, 1)
    response = client.post(url, correct_data, follow=True)

    assert response.status_code == 200
    assert response.redirect_chain == [(bdese_step_url(bdese, 2), 302)]

    content = response.content.decode("utf-8")
    assert "Étape enregistrée" in content

    bdese.refresh_from_db()
    if bdese.is_bdese_300:
        assert bdese.unite_absenteisme == "H"
    else:
        assert bdese.effectif_cdi == 50
    assert bdese.step_is_complete(1)


def test_mark_step_as_incomplete(configured_bdese, habilitated_user, client):
    bdese = configured_bdese
    bdese.mark_step_as_complete(1)
    bdese.save()

    bdese.refresh_from_db()
    assert bdese.step_is_complete(1)

    client.force_login(habilitated_user)

    url = bdese_step_url(bdese, 1)
    response = client.post(url, {"mark_incomplete": ""}, follow=True)

    assert response.status_code == 200
    assert response.redirect_chain == [(url, 302)]

    content = response.content.decode("utf-8")
    assert "Étape enregistrée" not in content
    assert "Enregistrer et marquer comme terminé" in content
    assert "Enregistrer en brouillon" in content

    bdese.refresh_from_db()
    assert not bdese.step_is_complete(1)


@pytest.mark.slow
def test_get_pdf(bdese, habilitated_user, client):
    client.force_login(habilitated_user)

    url = f"/bdese/{bdese.entreprise.siren}/{bdese.annee}/pdf"
    response = client.get(url)

    assert response.status_code == 200


def test_render_bdese_pdf_html(configured_bdese):
    bdese = configured_bdese
    if bdese.is_bdese_300:
        bdese.external_fields = ["effectif_total"]
        bdese.effectif_permanent = {
            category: 10 for category in bdese.categories_professionnelles
        }
    else:
        bdese.external_fields = ["effectif_mensuel"]
        bdese.effectif_homme = {
            category: 10 for category in bdese.categories_professionnelles
        }

    pdf_html = render_bdese_pdf_html(bdese)

    assert bdese.entreprise.raison_sociale in pdf_html
    assert str(bdese.annee) in pdf_html
    for category in bdese.categories_professionnelles:
        assert category.capitalize() in pdf_html
    assert "Cette information est remplie dans un autre document." in pdf_html
    assert "Information non remplie." in pdf_html


def test_get_bdese_configuration(bdese, habilitated_user, client):
    client.force_login(habilitated_user)

    url = bdese_step_url(bdese, 0)
    response = client.get(url)

    assert response.status_code == 200


def test_save_bdese_configuration(bdese, habilitated_user, client):
    client.force_login(habilitated_user)

    categories_pro = ["catégorie 1", "catégorie 2", "catégorie 3"]
    categories_pro_detaillees = [
        "catégorie détaillée 1",
        "catégorie détaillée 2",
        "catégorie détaillée 3",
        "catégorie détaillée 4",
        "catégorie détaillée 5",
    ]
    niveaux_hierarchiques = ["niveau 1", "niveau 2"]
    data = configuration_form_data(
        categories_pro, categories_pro_detaillees, niveaux_hierarchiques
    )

    url = bdese_step_url(bdese, 0)
    response = client.post(
        url,
        data=data,
        follow=True,
    )

    assert response.status_code == 200
    assert response.redirect_chain == [(url, 302)]

    content = response.content.decode("utf-8")
    assert "Étape enregistrée" in content

    bdese.refresh_from_db()
    assert bdese.categories_professionnelles == categories_pro
    if bdese.is_bdese_300:
        assert bdese.categories_professionnelles_detaillees == categories_pro_detaillees
        assert bdese.niveaux_hierarchiques == niveaux_hierarchiques
    assert bdese.is_configured
    assert not bdese.step_is_complete(0)


def test_save_and_complete_bdese_configuration(bdese, habilitated_user, client):
    client.force_login(habilitated_user)

    categories_pro = ["catégorie 1", "catégorie 2", "catégorie 3"]
    categories_pro_detaillees = [
        "catégorie détaillée 1",
        "catégorie détaillée 2",
        "catégorie détaillée 3",
        "catégorie détaillée 4",
        "catégorie détaillée 5",
    ]
    niveaux_hierarchiques = ["niveau 1", "niveau 2"]
    data = configuration_form_data(
        categories_pro, categories_pro_detaillees, niveaux_hierarchiques
    )
    data.update({"save_complete": ""})

    url = bdese_step_url(bdese, 0)
    response = client.post(
        url,
        data=data,
        follow=True,
    )

    assert response.status_code == 200
    assert response.redirect_chain == [(bdese_step_url(bdese, 1), 302)]

    content = response.content.decode("utf-8")
    assert "Étape enregistrée" in content

    bdese.refresh_from_db()
    assert bdese.categories_professionnelles == categories_pro
    if bdese.is_bdese_300:
        assert bdese.categories_professionnelles_detaillees == categories_pro_detaillees
        assert bdese.niveaux_hierarchiques == niveaux_hierarchiques
    assert bdese.is_configured
    assert bdese.step_is_complete(0)


def test_mark_as_incomplete_bdese_configuration(
    configured_bdese, habilitated_user, client
):
    bdese = configured_bdese
    categories_pro = bdese.categories_professionnelles
    if bdese.is_bdese_300:
        categories_pro_detaillees = bdese.categories_professionnelles_detaillees
        niveaux_hierarchiques = bdese.niveaux_hierarchiques
    client.force_login(habilitated_user)

    url = bdese_step_url(bdese, 0)
    response = client.post(
        url,
        data={"mark_incomplete": ""},
        follow=True,
    )

    assert response.status_code == 200
    assert response.redirect_chain == [(url, 302)]

    content = response.content.decode("utf-8")
    assert "Étape enregistrée" not in content

    bdese.refresh_from_db()
    assert bdese.categories_professionnelles == categories_pro
    if bdese.is_bdese_300:
        assert bdese.categories_professionnelles_detaillees == categories_pro_detaillees
        assert bdese.niveaux_hierarchiques == niveaux_hierarchiques
    assert bdese.is_configured
    assert not bdese.step_is_complete(0)


def test_save_bdese_configuration_error(bdese, habilitated_user, client):
    categories_pro = ["catégorie 1", "catégorie 2"]
    client.force_login(habilitated_user)

    url = bdese_step_url(bdese, 0)
    response = client.post(url, data=configuration_form_data(categories_pro))

    assert response.status_code == 200

    content = html.unescape(response.content.decode("utf-8"))
    assert (
        "L'étape n'a pas été enregistrée car le formulaire contient des erreurs"
        in content
    )
    assert "Au moins 3 postes sont requis" in content

    bdese.refresh_from_db()
    assert not bdese.categories_professionnelles
    assert not bdese.is_configured


def test_save_bdese_configuration_for_a_new_year(
    configured_bdese, habilitated_user, client
):
    categories_pro = configured_bdese.categories_professionnelles
    if configured_bdese.is_bdese_300:
        categories_pro_detaillees = (
            configured_bdese.categories_professionnelles_detaillees
        )
        niveaux_hierarchiques = configured_bdese.niveaux_hierarchiques
    client.force_login(habilitated_user)

    new_year = configured_bdese.annee + 1

    url = f"/bdese/{configured_bdese.entreprise.siren}/{new_year}/0"
    response = client.get(url)

    # le formulaire est initialisé avec la configuration de la dernière bdese configurée
    content = response.content.decode("utf-8")
    for categorie in categories_pro:
        assert categorie in content
    if configured_bdese.is_bdese_300:
        for categorie in categories_pro_detaillees:
            assert categorie in content
        for niveau in niveaux_hierarchiques:
            assert niveau in niveaux_hierarchiques
    assert "Enregistrer et marquer comme terminé" in content, content
    assert "Enregistrer en brouillon" in content

    new_categories_pro = ["A", "B", "C", "D"]
    new_categories_pro_detaillees = ["E", "F", "G", "H", "I"]
    new_niveaux_hierarchiques = ["Y", "Z"]
    response = client.post(
        url,
        data=configuration_form_data(
            new_categories_pro, new_categories_pro_detaillees, new_niveaux_hierarchiques
        ),
        follow=True,
    )

    assert response.status_code == 200
    assert response.redirect_chain == [
        (reverse("bdese", args=[configured_bdese.entreprise.siren, new_year, 0]), 302)
    ]

    content = response.content.decode("utf-8")
    assert "Étape enregistrée" in content

    configured_bdese.refresh_from_db()
    new_bdese = configured_bdese.__class__.objects.get(
        entreprise=configured_bdese.entreprise, annee=new_year
    )
    assert configured_bdese.categories_professionnelles == categories_pro
    assert new_bdese.categories_professionnelles == new_categories_pro
    if configured_bdese.is_bdese_300:
        assert (
            configured_bdese.categories_professionnelles_detaillees
            == categories_pro_detaillees
        )
        assert (
            new_bdese.categories_professionnelles_detaillees
            == new_categories_pro_detaillees
        )
        assert configured_bdese.niveaux_hierarchiques == niveaux_hierarchiques
        assert new_bdese.niveaux_hierarchiques == new_niveaux_hierarchiques
    assert new_bdese.is_configured


class MockedResponse:
    def __init__(self, content, status_code):
        self.content = content
        self.status_code = status_code

    def json(self):
        return json.loads(self.content)


def test_get_bdese_data_from_egapro_with_only_one_objectif_de_progression(
    grande_entreprise, mocker
):
    # Example response inspired from https://egapro.travail.gouv.fr/api/public/declaration/552032534/2021
    index_egapro_data = """{"entreprise":{"siren":"552032534","r\u00e9gion":"\u00cele-de-France","code_naf":"70.10Z","effectif":{"total":867,"tranche":"251:999"},"d\u00e9partement":"Paris","raison_sociale":"DANONE"},"indicateurs":{"promotions":{"non_calculable":null,"note":15,"objectif_de_progression":null},"augmentations_et_promotions":{"non_calculable":null,"note":null,"objectif_de_progression":null},"r\u00e9mun\u00e9rations":{"non_calculable":null,"note":29,"objectif_de_progression":null},"cong\u00e9s_maternit\u00e9":{"non_calculable":null,"note":15,"objectif_de_progression":null},"hautes_r\u00e9mun\u00e9rations":{"non_calculable":null,"note":0,"objectif_de_progression":"plus dans le futur","r\u00e9sultat":1,"population_favorable":"femmes"}},"d\u00e9claration":{"index":79,"ann\u00e9e_indicateurs":2021,"mesures_correctives":null}}"""

    egapro_request = mocker.patch(
        "requests.get", return_value=MockedResponse(index_egapro_data, 200)
    )

    bdese_data_from_egapro = get_bdese_data_from_egapro(grande_entreprise, 2021)

    assert bdese_data_from_egapro == {
        "nombre_femmes_plus_hautes_remunerations": 9,
        "objectifs_progression": "Hautes rémunérations : plus dans le futur",
    }
    egapro_request.assert_called_once_with(
        f"https://egapro.travail.gouv.fr/api/public/declaration/{grande_entreprise.siren}/2021"
    )


def test_get_bdese_data_from_egapro_without_objectif_de_progression(
    grande_entreprise, mocker
):
    # Example response inspired from https://egapro.travail.gouv.fr/api/public/declaration/552032534/2021
    index_egapro_data = """{"entreprise":{"siren":"552032534","r\u00e9gion":"\u00cele-de-France","code_naf":"70.10Z","effectif":{"total":867,"tranche":"251:999"},"d\u00e9partement":"Paris","raison_sociale":"DANONE"},"indicateurs":{"promotions":{"non_calculable":null,"note":15,"objectif_de_progression":null},"augmentations_et_promotions":{"non_calculable":null,"note":null,"objectif_de_progression":null},"r\u00e9mun\u00e9rations":{"non_calculable":null,"note":29,"objectif_de_progression":null},"cong\u00e9s_maternit\u00e9":{"non_calculable":null,"note":15,"objectif_de_progression":null},"hautes_r\u00e9mun\u00e9rations":{"non_calculable":null,"note":0,"objectif_de_progression":null,"r\u00e9sultat":1,"population_favorable":"femmes"}},"d\u00e9claration":{"index":79,"ann\u00e9e_indicateurs":2021,"mesures_correctives":null}}"""

    egapro_request = mocker.patch(
        "requests.get", return_value=MockedResponse(index_egapro_data, 200)
    )

    bdese_data_from_egapro = get_bdese_data_from_egapro(grande_entreprise, 2021)

    assert bdese_data_from_egapro["objectifs_progression"] == None


def test_get_bdese_data_from_egapro_with_all_objectifs_de_progression(
    grande_entreprise, mocker
):
    # Example response inspired from https://egapro.travail.gouv.fr/api/public/declaration/552032534/2021
    index_egapro_data = """{"entreprise":{"siren":"552032534","r\u00e9gion":"\u00cele-de-France","code_naf":"70.10Z","effectif":{"total":867,"tranche":"251:999"},"d\u00e9partement":"Paris","raison_sociale":"DANONE"},"indicateurs":{"promotions":{"non_calculable":null,"note":15,"objectif_de_progression":"P1"},"augmentations_et_promotions":{"non_calculable":null,"note":null,"objectif_de_progression":"P2"},"r\u00e9mun\u00e9rations":{"non_calculable":null,"note":29,"objectif_de_progression":"P3"},"cong\u00e9s_maternit\u00e9":{"non_calculable":null,"note":15,"objectif_de_progression":"P4"},"hautes_r\u00e9mun\u00e9rations":{"non_calculable":null,"note":0,"objectif_de_progression":"P5","r\u00e9sultat":1,"population_favorable":"femmes"}},"d\u00e9claration":{"index":79,"ann\u00e9e_indicateurs":2021,"mesures_correctives":null}}"""

    egapro_request = mocker.patch(
        "requests.get", return_value=MockedResponse(index_egapro_data, 200)
    )

    bdese_data_from_egapro = get_bdese_data_from_egapro(grande_entreprise, 2021)

    assert (
        bdese_data_from_egapro["objectifs_progression"]
        == "Écart taux promotion : P1\nÉcart taux d'augmentation : P2\nÉcart rémunérations : P3\nRetour congé maternité : P4\nHautes rémunérations : P5"
    )


def test_get_bdese_data_from_egapro_with_no_result(grande_entreprise, mocker):
    # Example response from https://egapro.travail.gouv.fr/api/public/declaration/552032534/1990
    index_egapro_data = (
        """{"error":"No declaration with siren 552032534 and year 1990"}"""
    )

    egapro_request = mocker.patch(
        "requests.get", return_value=MockedResponse(index_egapro_data, 200)
    )

    bdese_data_from_egapro = get_bdese_data_from_egapro(grande_entreprise, 1990)

    assert bdese_data_from_egapro == {
        "nombre_femmes_plus_hautes_remunerations": None,
        "objectifs_progression": None,
    }
