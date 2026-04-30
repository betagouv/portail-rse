from django.urls import reverse

from vsme.models import RapportVSME


def test_telechargement_d_un_rapport_vsme_au_format_pptx_est_privé(
    client, entreprise_factory, alice, bob
):
    entreprise = entreprise_factory(utilisateur=alice)
    rapport_vsme = RapportVSME.objects.create(entreprise=entreprise, annee=2026)
    url = f"/vsme/{rapport_vsme.id}/export/pptx"

    # non connecté
    response = client.get(url)

    assert response.status_code == 302
    connexion_url = reverse("users:login")
    assert response.url == f"{connexion_url}?next={url}"

    # connecté mais non membre de l'entreprise
    client.force_login(bob)

    response = client.get(f"/vsme/{rapport_vsme.id}/export/pptx")

    assert response.status_code == 403


def test_telechargement_d_un_rapport_vsme_au_format_pptx(
    client, entreprise_factory, alice
):
    entreprise = entreprise_factory(utilisateur=alice)
    rapport_vsme = RapportVSME.objects.create(entreprise=entreprise, annee=2026)

    client.force_login(alice)

    response = client.get(f"/vsme/{rapport_vsme.id}/export/pptx")

    assert response["Content-Disposition"] == "filename=vsme.pptx"
    assert (
        response["content-type"]
        == "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )
