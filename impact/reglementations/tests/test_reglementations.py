def test_index(client):
    response = client.get("/reglementations")

    assert response.status_code == 200
    assert "<!-- page reglementations -->" in str(response.content)
