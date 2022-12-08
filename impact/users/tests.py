def test_page_creation(client):
    response = client.get("/creation")

    assert response.status_code == 200
    assert "<!-- page creation compte -->" in str(response.content)