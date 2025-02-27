def test_analyse_reussie(client):
    id_document = "42"
    url = f"/ESRS-predict/{id_document}"

    response = client.post(url)

    assert response.status_code == 200
