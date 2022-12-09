from django.urls import reverse
import pytest

from reglementations.models import annees_a_remplir_bdese, BDESE_50_300, BDESE_300
from reglementations.tests.test_bdese_forms import categories_form_data


def test_bdese_is_not_public(client, django_user_model, grande_entreprise):
    url = f"/bdese/{grande_entreprise.siren}/2022/1"
    response = client.get(url)

    assert response.status_code == 302
    connexion_url = reverse("login")
    assert response.url == f"{connexion_url}?next={url}"

    user = django_user_model.objects.create()
    client.force_login(user)
    response = client.get(url)

    assert response.status_code == 403


@pytest.mark.parametrize(
    "effectif, bdese_class", [("moyen", BDESE_50_300), ("grand", BDESE_300)]
)
def test_yearly_bdese_is_created_at_first_authorized_request(
    effectif, bdese_class, client, django_user_model, entreprise_factory
):
    entreprise = entreprise_factory(effectif=effectif)
    user = django_user_model.objects.create()
    entreprise.users.add(user)
    client.force_login(user)

    assert not bdese_class.objects.filter(entreprise=entreprise)

    url = f"/bdese/{entreprise.siren}/2021/1"
    response = client.get(url)

    assert response.status_code == 302
    bdese_2021 = bdese_class.objects.get(entreprise=entreprise, annee=2021)

    url = f"/bdese/{entreprise.siren}/2022/1"
    response = client.get(url)

    bdese_2022 = bdese_class.objects.get(entreprise=entreprise, annee=2022)
    assert bdese_2021 != bdese_2022


@pytest.fixture
def authorized_user(bdese, django_user_model):
    user = django_user_model.objects.create()
    bdese.entreprise.users.add(user)
    return user


def test_bdese_step_redirect_to_categories_professionnelles_if_not_filled(
    bdese, authorized_user, client
):
    client.force_login(authorized_user)

    url = f"/bdese/{bdese.entreprise.siren}/{bdese.annee}/1"
    response = client.get(url)

    assert response.status_code == 302
    assert response.url == reverse(
        "categories_professionnelles", args=[bdese.entreprise.siren, bdese.annee]
    )


def test_bdese_step_use_categories_professionnelles_and_annees_a_remplir(
    bdese, authorized_user, client
):
    categories_professionnelles = ["catégorie 1", "catégorie 2", "catégorie 3"]
    bdese.categories_professionnelles = categories_professionnelles
    bdese.save()
    client.force_login(authorized_user)

    url = f"/bdese/{bdese.entreprise.siren}/2022/1"
    response = client.get(url)

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    for category in categories_professionnelles:
        assert category in content
    for annee in annees_a_remplir_bdese():
        assert str(annee) in content


@pytest.fixture
def bdese_300_with_categories(bdese_factory):
    bdese = bdese_factory(bdese_class=BDESE_300)
    bdese.categories_professionnelles = ["catégorie 1", "catégorie 2", "catégorie 3"]
    bdese.categories_professionnelles_detaillees = [
        "catégorie détaillée 1",
        "catégorie détaillée 2",
        "catégorie détaillée 3",
        "catégorie détaillée 4",
        "catégorie détaillée 5",
    ]
    bdese.save()
    return bdese


def test_bdese_300_step_use_categories_professionnelles_detaillees(
    bdese_300_with_categories, django_user_model, client
):
    bdese = bdese_300_with_categories
    user = django_user_model.objects.create()
    bdese.entreprise.users.add(user)
    client.force_login(user)

    url = f"/bdese/{bdese.entreprise.siren}/2022/1"
    response = client.get(url)

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    for category in bdese.categories_professionnelles_detaillees:
        assert category in content


def test_save_step_error(bdese_300_with_categories, django_user_model, client):
    bdese = bdese_300_with_categories
    user = django_user_model.objects.create()
    bdese.entreprise.users.add(user)
    client.force_login(user)

    url = f"/bdese/{bdese.entreprise.siren}/{bdese.annee}/1"
    response = client.post(url, {"unite_absenteisme": "yolo"})

    assert response.status_code == 200
    assert (
        "L&#x27;étape n&#x27;a pas été enregistrée car le formulaire contient des erreurs"
        in response.content.decode("utf-8")
    )

    bdese.refresh_from_db()
    assert bdese.unite_absenteisme != "yolo"


def test_save_step_as_draft_success(
    bdese_300_with_categories, django_user_model, client
):
    bdese = bdese_300_with_categories
    user = django_user_model.objects.create()
    bdese.entreprise.users.add(user)
    client.force_login(user)

    url = f"/bdese/{bdese.entreprise.siren}/{bdese.annee}/1"
    response = client.post(url, {"unite_absenteisme": "H"})

    assert response.status_code == 200

    content = response.content.decode("utf-8")
    assert "Étape enregistrée" in content
    assert "Enregistrer et marquer comme terminé" in content
    assert "Enregistrer en brouillon" in content

    bdese.refresh_from_db()
    assert bdese.unite_absenteisme == "H"
    assert not bdese.step_is_complete(1)


def test_save_step_and_mark_as_complete_success(
    bdese_300_with_categories, django_user_model, client
):
    bdese = bdese_300_with_categories
    user = django_user_model.objects.create()
    bdese.entreprise.users.add(user)
    client.force_login(user)

    url = f"/bdese/{bdese.entreprise.siren}/{bdese.annee}/1"
    response = client.post(
        url, {"unite_absenteisme": "H", "save_complete": ""}, follow=True
    )

    assert response.status_code == 200
    assert response.redirect_chain == [(url, 302)]

    content = response.content.decode("utf-8")
    assert "Étape enregistrée" in content
    assert "Repasser en brouillon pour modifier" in content

    bdese.refresh_from_db()
    assert bdese.unite_absenteisme == "H"
    assert bdese.step_is_complete(1)


def test_mark_step_as_incomplete(bdese_300_with_categories, django_user_model, client):
    bdese = bdese_300_with_categories
    bdese.mark_step_as_complete(1)
    bdese.save()

    bdese.refresh_from_db()
    assert bdese.step_is_complete(1)

    user = django_user_model.objects.create()
    bdese.entreprise.users.add(user)
    client.force_login(user)

    url = f"/bdese/{bdese.entreprise.siren}/{bdese.annee}/1"
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
def test_get_pdf(bdese, authorized_user, client):
    client.force_login(authorized_user)

    url = f"/bdese/{bdese.entreprise.siren}/{bdese.annee}/pdf"
    response = client.get(url)

    assert response.status_code == 200


def test_get_categories_professionnelles(bdese, authorized_user, client):
    client.force_login(authorized_user)

    url = f"/bdese/{bdese.entreprise.siren}/{bdese.annee}/0"
    response = client.get(url)

    assert response.status_code == 200


def test_save_categories_professionnelles(bdese, authorized_user, client):
    client.force_login(authorized_user)

    categories_pro = ["catégorie 1", "catégorie 2", "catégorie 3"]
    categories_pro_detaillees = [
        "catégorie détaillée 1",
        "catégorie détaillée 2",
        "catégorie détaillée 3",
        "catégorie détaillée 4",
        "catégorie détaillée 5",
    ]
    url = f"/bdese/{bdese.entreprise.siren}/{bdese.annee}/0"
    response = client.post(
        url,
        data=categories_form_data(categories_pro, categories_pro_detaillees),
        follow=True,
    )

    assert response.status_code == 200
    assert response.redirect_chain == [
        (reverse("bdese", args=[bdese.entreprise.siren, bdese.annee, 1]), 302)
    ]

    content = response.content.decode("utf-8")
    assert "Catégories enregistrées" in content

    bdese.refresh_from_db()
    assert bdese.categories_professionnelles == categories_pro
    if bdese.is_bdese_300:
        assert bdese.categories_professionnelles_detaillees == categories_pro_detaillees


def test_save_categories_professionnelles_error(bdese, authorized_user, client):
    categories_pro = ["catégorie 1", "catégorie 2"]
    client.force_login(authorized_user)

    url = f"/bdese/{bdese.entreprise.siren}/{bdese.annee}/0"
    response = client.post(url, data=categories_form_data(categories_pro))

    assert response.status_code == 200

    content = response.content.decode("utf-8")
    assert "Au moins 3 catégories sont requises" in content

    bdese.refresh_from_db()
    assert not bdese.categories_professionnelles


def test_save_categories_professionnelles_for_a_new_year(
    bdese, authorized_user, client
):
    categories_pro = ["catégorie 1", "catégorie 2", "catégorie 3"]
    categories_pro_detaillees = [
        "catégorie détaillée 1",
        "catégorie détaillée 2",
        "catégorie détaillée 3",
        "catégorie détaillée 4",
        "catégorie détaillée 5",
    ]
    bdese.categories_professionnelles = categories_pro
    if bdese.is_bdese_300:
        bdese.categories_professionnelles_detaillees = categories_pro_detaillees
    bdese.save()
    client.force_login(authorized_user)

    new_year = bdese.annee + 1

    url = f"/bdese/{bdese.entreprise.siren}/{new_year}/0"
    response = client.get(url)

    content = response.content.decode("utf-8")
    for categorie in categories_pro:
        assert categorie in content
    if bdese.is_bdese_300:
        for categorie in categories_pro_detaillees:
            assert categorie in content

    new_categories_pro = ["A", "B", "C", "D"]
    new_categories_pro_detaillees = ["E", "F", "G", "H", "I"]
    response = client.post(
        url,
        data=categories_form_data(new_categories_pro, new_categories_pro_detaillees),
        follow=True,
    )

    assert response.status_code == 200
    assert response.redirect_chain == [
        (reverse("bdese", args=[bdese.entreprise.siren, new_year, 1]), 302)
    ]

    content = response.content.decode("utf-8")
    assert "Catégories enregistrées" in content

    bdese.refresh_from_db()
    new_bdese = bdese.__class__.objects.get(entreprise=bdese.entreprise, annee=new_year)
    assert bdese.categories_professionnelles == categories_pro
    assert new_bdese.categories_professionnelles == new_categories_pro
    if bdese.is_bdese_300:
        assert bdese.categories_professionnelles_detaillees == categories_pro_detaillees
        assert (
            new_bdese.categories_professionnelles_detaillees
            == new_categories_pro_detaillees
        )
