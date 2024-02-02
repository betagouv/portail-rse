import html

import pytest
from django.urls import reverse

from entreprises.exceptions import EntrepriseNonQualifieeError
from entreprises.models import CaracteristiquesAnnuelles
from habilitations.models import attach_user_to_entreprise
from reglementations.models import annees_a_remplir_bdese
from reglementations.models import BDESE_300
from reglementations.models import BDESE_50_300
from reglementations.tests.test_bdese_forms import configuration_form_data
from reglementations.views.bdese import get_or_create_bdese
from reglementations.views.bdese import initialize_bdese_configuration
from reglementations.views.bdese import render_bdese_pdf_html


def test_bdese_is_not_public(client, alice, grande_entreprise):
    url = f"/bdese/{grande_entreprise.siren}/2022/1"
    response = client.get(url)

    assert response.status_code == 302
    connexion_url = reverse("users:login")
    assert response.url == f"{connexion_url}?next={url}"

    client.force_login(alice)
    response = client.get(url)

    assert response.status_code == 403


@pytest.mark.parametrize(
    "effectif, bdese_class",
    [
        (CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249, BDESE_50_300),
        (CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_299, BDESE_50_300),
        (CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499, BDESE_300),
    ],
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


def test_bdese_step_introuvable_si_bdese_avec_accord(bdese_avec_accord, alice, client):
    client.force_login(alice)
    entreprise = bdese_avec_accord.entreprise

    url = bdese_step_url(bdese_avec_accord, 1)
    response = client.get(url)

    assert response.status_code == 404


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
                "reglementations:bdese_step",
                args=[bdese.entreprise.siren, bdese.annee, 0],
            ),
            302,
        )
    ]
    assert (
        f"Commencez par configurer votre BDESE {bdese.annee}"
        in response.content.decode("utf-8")
    )


@pytest.mark.parametrize(
    "effectif, affichage_non_soumis",
    [
        (CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50, True),
        (CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249, False),
        (CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_299, False),
        (CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499, False),
        (CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999, False),
        (CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999, False),
        (CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS, False),
    ],
)
def test_étape_bdese_affiche_un_message_indiquant_non_soumis_le_cas_échéant(
    effectif, affichage_non_soumis, bdese, habilitated_user, client
):
    caracteristiques = bdese.entreprise.dernieres_caracteristiques_qualifiantes
    print(("CARAC", caracteristiques, caracteristiques.annee))
    caracteristiques.effectif = effectif
    caracteristiques.save()

    client.force_login(habilitated_user)

    url = bdese_step_url(bdese, 1)
    response = client.get(url, follow=True)

    assert response.status_code == 200
    assert response.redirect_chain == [
        (
            reverse(
                "reglementations:bdese_step",
                args=[bdese.entreprise.siren, bdese.annee, 0],
            ),
            302,
        )
    ]
    assert (
        "Ceci est une démonstration de la BDESE : vous n'êtes actuellement pas soumis à cette réglementation."
        in response.content.decode("utf-8")
    ) == affichage_non_soumis


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
    attach_user_to_entreprise(bob, bdese.entreprise, "Vice-président")
    client.force_login(bob)

    url = bdese_step_url(bdese, 0)
    response = client.get(url)

    assert response.status_code == 200
    content = html.unescape(response.content.decode("utf-8"))
    assert (
        "Plusieurs utilisateurs sont liés à cette entreprise. Les informations que vous remplissez ne sont pas partagées avec les autres utilisateurs tant que vous n'êtes pas habilités."
        in content
    )

    client.force_login(habilitated_user)

    response = client.get(url)

    assert response.status_code == 200
    content = html.unescape(response.content.decode("utf-8"))
    assert (
        "Plusieurs utilisateurs sont liés à cette entreprise. Les informations que vous remplissez ne sont pas partagées avec les autres utilisateurs tant que vous n'êtes pas habilités."
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

    fetch_data = mocker.patch("api.egapro.indicateurs_bdese")

    url = bdese_step_url(bdese, 1)
    client.get(url)

    fetch_data.assert_called_once_with(bdese.entreprise.siren, bdese.annee)


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


def test_get_pdf_redirige_vers_la_qualification_si_manquante(
    bdese, habilitated_user, client
):
    client.force_login(habilitated_user)
    entreprise = bdese.entreprise
    entreprise.caracteristiques_annuelles(bdese.annee).delete()
    url = f"/bdese/{entreprise.siren}/{bdese.annee}/pdf"

    response = client.get(url)

    assert response.status_code == 302
    assert response.url == reverse("entreprises:qualification", args=[entreprise.siren])


def test_get_pdf_introuvable_si_bdese_avec_accord(bdese_avec_accord, alice, client):
    client.force_login(alice)

    url = f"/bdese/{bdese_avec_accord.entreprise.siren}/{bdese_avec_accord.annee}/pdf"
    response = client.get(url)

    assert response.status_code == 404


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

    assert bdese.entreprise.denomination in pdf_html
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
        (
            reverse(
                "reglementations:bdese_step",
                args=[configured_bdese.entreprise.siren, new_year, 0],
            ),
            302,
        )
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


@pytest.mark.parametrize("bdese_class", [BDESE_50_300, BDESE_300])
def test_initialize_personal_bdese_configuration_only_with_other_personal_bdeses(
    bdese_class, bdese_factory, alice
):
    official_bdese = bdese_factory(bdese_class=bdese_class, annee=2021)
    official_bdese.categories_professionnelles = ["A", "B", "C"]
    if official_bdese.is_bdese_300:
        official_bdese.categories_professionnelles_detaillees = [
            "E",
            "F",
            "G",
            "H",
            "I",
        ]
        official_bdese.niveaux_hierarchiques = ["Y", "Z"]
    official_bdese.save()

    new_bdese = bdese_factory(
        bdese_class, entreprise=official_bdese.entreprise, user=alice, annee=2022
    )
    initial = initialize_bdese_configuration(new_bdese)

    assert not initial

    personal_bdese = bdese_factory(
        bdese_class=bdese_class,
        entreprise=official_bdese.entreprise,
        user=alice,
        annee=2021,
    )
    personal_bdese.categories_professionnelles = ["A", "B", "C"]
    if personal_bdese.is_bdese_300:
        personal_bdese.categories_professionnelles_detaillees = [
            "E",
            "F",
            "G",
            "H",
            "I",
        ]
        personal_bdese.niveaux_hierarchiques = ["Y", "Z"]
    personal_bdese.save()

    initial = initialize_bdese_configuration(new_bdese)

    assert initial["categories_professionnelles"] == ["A", "B", "C"]
    if personal_bdese.is_bdese_300:
        assert initial["categories_professionnelles_detaillees"] == [
            "E",
            "F",
            "G",
            "H",
            "I",
        ]
        assert initial["niveaux_hierarchiques"] == ["Y", "Z"]


@pytest.mark.parametrize("bdese_class", [BDESE_50_300, BDESE_300])
def test_initialize_official_bdese_configuration_only_with_other_official_bdeses(
    bdese_class, bdese_factory, alice
):
    personal_bdese = bdese_factory(bdese_class=bdese_class, user=alice, annee=2021)
    personal_bdese.categories_professionnelles = ["A", "B", "C"]
    if personal_bdese.is_bdese_300:
        personal_bdese.categories_professionnelles_detaillees = [
            "E",
            "F",
            "G",
            "H",
            "I",
        ]
        personal_bdese.niveaux_hierarchiques = ["Y", "Z"]
    personal_bdese.save()

    new_bdese = bdese_factory(
        bdese_class, entreprise=personal_bdese.entreprise, annee=2022
    )
    initial = initialize_bdese_configuration(new_bdese)

    assert not initial

    official_bdese = bdese_factory(
        bdese_class=bdese_class, entreprise=personal_bdese.entreprise, annee=2021
    )
    official_bdese.categories_professionnelles = ["A", "B", "C"]
    if official_bdese.is_bdese_300:
        official_bdese.categories_professionnelles_detaillees = [
            "E",
            "F",
            "G",
            "H",
            "I",
        ]
        official_bdese.niveaux_hierarchiques = ["Y", "Z"]
    official_bdese.save()

    initial = initialize_bdese_configuration(new_bdese)

    assert initial["categories_professionnelles"] == ["A", "B", "C"]
    if personal_bdese.is_bdese_300:
        assert initial["categories_professionnelles_detaillees"] == [
            "E",
            "F",
            "G",
            "H",
            "I",
        ]
        assert initial["niveaux_hierarchiques"] == ["Y", "Z"]


def test_toggle_bdese_completion(client, bdese_avec_accord, alice):
    client.force_login(alice)
    entreprise = bdese_avec_accord.entreprise
    url = (
        f"/bdese/{entreprise.siren}/{bdese_avec_accord.annee}/actualiser-desactualiser"
    )

    response = client.get(url, follow=True)

    assert response.status_code == 200
    assert response.redirect_chain == [
        (reverse("reglementations:tableau_de_bord", args=[entreprise.siren]), 302)
    ]
    bdese_avec_accord.refresh_from_db()
    assert bdese_avec_accord.is_complete

    response = client.get(url, follow=True)

    bdese_avec_accord.refresh_from_db()
    assert not bdese_avec_accord.is_complete


def test_toggle_bdese_completion_redirige_vers_la_qualification_si_manquante(
    bdese, habilitated_user, client
):
    client.force_login(habilitated_user)
    entreprise = bdese.entreprise
    entreprise.caracteristiques_annuelles(bdese.annee).delete()
    url = f"/bdese/{entreprise.siren}/{bdese.annee}/actualiser-desactualiser"

    response = client.get(url)

    assert response.status_code == 302
    assert response.url == reverse("entreprises:qualification", args=[entreprise.siren])


def test_get_or_create_bdese_avec_une_entreprise_non_qualifiee(
    entreprise_non_qualifiee, alice
):
    attach_user_to_entreprise(alice, entreprise_non_qualifiee, "Présidente")

    with pytest.raises(EntrepriseNonQualifieeError):
        get_or_create_bdese(entreprise_non_qualifiee, 2023, alice)
