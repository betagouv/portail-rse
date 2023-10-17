def test_page_fiche_audit_energetique(client):
    response = client.get("/reglementations/fiches/audit-energetique")

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "<!-- page fiche audit energetique -->" in content


def test_page_fiche_bdese(client):
    response = client.get("/reglementations/fiches/bdese")

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "<!-- page fiche BDESE -->" in content
