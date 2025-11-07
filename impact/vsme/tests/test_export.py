from io import BytesIO

from django.urls import reverse
from openpyxl import load_workbook

from vsme.models import Indicateur
from vsme.models import RapportVSME


def test_telechargement_d_un_rapport_vsme_au_format_xlsx(
    client, entreprise_factory, alice
):
    entreprise = entreprise_factory(utilisateur=alice)
    rapport_vsme = RapportVSME.objects.create(entreprise=entreprise, annee=2025)
    Indicateur.objects.create(
        rapport_vsme=rapport_vsme,
        schema_id="B2-26",
        data={
            "declaration_durabilite": {
                "changement_climatique": {
                    "pratiques": True,
                    "accessibles": True,
                    "cibles": False,
                },
                "pollution": {
                    "pratiques": False,
                    "accessibles": False,
                    "cibles": False,
                },
                "eau": {"pratiques": False, "accessibles": False, "cibles": True},
                "biodiversite": {
                    "pratiques": False,
                    "accessibles": False,
                    "cibles": False,
                },
                "economie_circulaire": {
                    "pratiques": False,
                    "accessibles": False,
                    "cibles": False,
                },
                "personnel": {
                    "pratiques": False,
                    "accessibles": False,
                    "cibles": False,
                },
                "travailleurs": {
                    "pratiques": False,
                    "accessibles": False,
                    "cibles": False,
                },
                "communautes": {
                    "pratiques": False,
                    "accessibles": False,
                    "cibles": False,
                },
                "consommateurs": {
                    "pratiques": False,
                    "accessibles": False,
                    "cibles": False,
                },
                "conduite_affaires": {
                    "pratiques": False,
                    "accessibles": True,
                    "cibles": True,
                },
            }
        },
    )
    client.force_login(alice)

    response = client.get(f"/vsme/{rapport_vsme.id}/export/xlsx")

    assert response["Content-Disposition"] == "filename=vsme.xlsx"
    assert (
        response["content-type"]
        == "application/vnd.openxmlformatsofficedocument.spreadsheetml.sheet"
    )
    workbook = load_workbook(filename=BytesIO(response.content))
    onglet_b2 = workbook["B2"]
    assert onglet_b2["C3"].value == "OUI"
    assert onglet_b2["D3"].value == "OUI"
    assert onglet_b2["E3"].value == "NON"
    assert onglet_b2["C12"].value == "NON"
    assert onglet_b2["D12"].value == "OUI"
    assert onglet_b2["E12"].value == "OUI"


def test_telechargement_d_un_rapport_vsme_inexistant(client, entreprise_factory, alice):
    entreprise = entreprise_factory(utilisateur=alice)
    client.force_login(alice)

    response = client.get(f"/vsme/42/export/xlsx")

    assert response.status_code == 404


def test_telechargement_d_un_rapport_vsme_redirige_vers_la_connexion_si_non_connecté(
    client, entreprise_factory, alice
):
    entreprise = entreprise_factory(utilisateur=alice)
    rapport_vsme = RapportVSME.objects.create(entreprise=entreprise, annee=2025)

    response = client.get(f"/vsme/{rapport_vsme.id}/export/xlsx")

    assert response.status_code == 302

    response = client.get(
        reverse("analyseia:synthese_resultat", args=[entreprise.siren, 42]),
    )

    assert response.status_code == 302
