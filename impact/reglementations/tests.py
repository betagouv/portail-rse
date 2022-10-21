from django.test import Client


def test_index():
    response = Client().get("/reglementations")

    assert response.status_code == 200
    assert "<!-- page reglementations -->" in str(response.content)
