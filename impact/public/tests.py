def test_index(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "<!-- page index -->" in str(response.content)
