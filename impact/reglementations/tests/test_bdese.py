from django.urls import reverse
import pytest

from reglementations.models import BDESE_50_300, BDESE_300


def test_bdese_is_not_public(client, django_user_model, entreprise):
    url = f"/bdese/{entreprise.siren}/1"
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
def test_bdese_is_created_at_first_authorized_request(
    effectif, bdese_class, client, django_user_model, entreprise_factory
):
    entreprise = entreprise_factory(effectif=effectif)
    user = django_user_model.objects.create()
    entreprise.users.add(user)
    client.force_login(user)

    assert not bdese_class.objects.filter(entreprise=entreprise)

    url = f"/bdese/{entreprise.siren}/1"
    response = client.get(url)

    assert response.status_code == 200
    bdese = bdese_class.objects.get(entreprise=entreprise)
