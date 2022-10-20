from django.test import Client


def test_index():
    response = Client().get("/")

    assert response.status_code == 200
    assert "<!-- page index -->" in str(response.content)
