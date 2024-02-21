from django.urls import reverse


def test_espace_csrd_is_not_public(client, alice):
    url = f"/csrd"
    response = client.get(url)

    assert response.status_code == 302
    connexion_url = reverse("users:login")
    assert response.url == f"{connexion_url}?next={url}"

    client.force_login(alice)
    response = client.get(url)

    assert response.status_code == 200
    assert response.templates[0].name == "reglementations/espace-csrd.html"
