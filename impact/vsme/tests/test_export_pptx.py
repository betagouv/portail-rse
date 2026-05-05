from pathlib import Path

from django.conf import settings
from django.urls import reverse
from pptx import Presentation

from vsme.export_pptx import export_pptx_exigence_de_publication
from vsme.models import EXIGENCES_DE_PUBLICATION
from vsme.models import Indicateur
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


def test_export_pptx_d_un_champ_nombre_entier(entreprise_factory, alice):
    entreprise = entreprise_factory(utilisateur=alice)
    rapport_vsme = RapportVSME.objects.create(entreprise=entreprise, annee=2026)
    indicateur = Indicateur(
        rapport_vsme=rapport_vsme,
        schema_id="B1-24-e-iii",  # bilan
        data={"bilan": 12345},
    )
    chemin_pptx = Path(settings.BASE_DIR, "vsme/exports/vsme.pptx")
    presentation = Presentation(chemin_pptx)

    export_pptx_exigence_de_publication(
        EXIGENCES_DE_PUBLICATION["B1"], presentation, {"B1-24-e-iii": indicateur}
    )

    shapes = presentation.slides[4].shapes
    for shape in shapes:
        if shape.name == "B1-24-e-iii":
            assert shape.text_frame.paragraphs[1].runs[0].text == "12345"


def test_export_pptx_d_un_champ_choix_unique(entreprise_factory, alice):
    entreprise = entreprise_factory(utilisateur=alice)
    rapport_vsme = RapportVSME.objects.create(entreprise=entreprise, annee=2026)
    indicateur = Indicateur(
        rapport_vsme=rapport_vsme,
        schema_id="B1-24-a",  # Base d’établissement
        data={"choix_module": "complet"},
    )
    chemin_pptx = Path(settings.BASE_DIR, "vsme/exports/vsme.pptx")
    presentation = Presentation(chemin_pptx)

    export_pptx_exigence_de_publication(
        EXIGENCES_DE_PUBLICATION["B1"], presentation, {"B1-24-a": indicateur}
    )

    shapes = presentation.slides[4].shapes
    for shape in shapes:
        if shape.name == "B1-24-a":
            assert shape.text_frame.paragraphs[1].runs[0].text == "Module complet"


def test_export_pptx_d_un_champ_choix_binaire(entreprise_factory, alice):
    entreprise = entreprise_factory(utilisateur=alice)
    rapport_vsme = RapportVSME.objects.create(entreprise=entreprise, annee=2026)
    indicateur = Indicateur(
        rapport_vsme=rapport_vsme,
        schema_id="B1-24-e-i",  # Forme juridique de l’entreprise
        data={"forme_juridique": "57", "coopérative": True},
    )
    chemin_pptx = Path(settings.BASE_DIR, "vsme/exports/vsme.pptx")
    presentation = Presentation(chemin_pptx)

    export_pptx_exigence_de_publication(
        EXIGENCES_DE_PUBLICATION["B1"], presentation, {"B1-24-e-i": indicateur}
    )

    shapes = presentation.slides[4].shapes
    for shape in shapes:
        if shape.name == "B1-24-e-i_coopérative":
            assert shape.text_frame.paragraphs[1].runs[0].text == "OUI"


def test_export_pptx_d_un_champ_choix_binaire__forme_juridique(
    entreprise_factory, alice
):
    entreprise = entreprise_factory(utilisateur=alice)
    rapport_vsme = RapportVSME.objects.create(entreprise=entreprise, annee=2026)
    indicateur = Indicateur(
        rapport_vsme=rapport_vsme,
        schema_id="B1-24-e-i",  # Forme juridique de l’entreprise
        data={"forme_juridique": "57", "coopérative": True},
    )
    chemin_pptx = Path(settings.BASE_DIR, "vsme/exports/vsme.pptx")
    presentation = Presentation(chemin_pptx)

    export_pptx_exigence_de_publication(
        EXIGENCES_DE_PUBLICATION["B1"], presentation, {"B1-24-e-i": indicateur}
    )

    shapes = presentation.slides[4].shapes
    for shape in shapes:
        if shape.name == "B1-24-e-i_forme_juridique":
            assert (
                shape.text_frame.paragraphs[1].runs[0].text
                == "Société par actions simplifiée (SAS)"
            )


def test_export_pptx_d_un_champ_choix_multiple(entreprise_factory, alice):
    entreprise = entreprise_factory(utilisateur=alice)
    rapport_vsme = RapportVSME.objects.create(entreprise=entreprise, annee=2026)
    indicateur = Indicateur(
        rapport_vsme=rapport_vsme,
        schema_id="B1-24-e-ii",  # Code(s) NACE
        data={"nace": ["03.11", "03.21", "03.30"]},
    )
    chemin_pptx = Path(settings.BASE_DIR, "vsme/exports/vsme.pptx")
    presentation = Presentation(chemin_pptx)

    export_pptx_exigence_de_publication(
        EXIGENCES_DE_PUBLICATION["B1"], presentation, {"B1-24-e-ii": indicateur}
    )

    shapes = presentation.slides[4].shapes
    for shape in shapes:
        if shape.name == "B1-24-e-ii":
            assert (
                shape.text_frame.paragraphs[1].runs[0].text
                == "Pêche en mer, Aquaculture en mer, Activités de soutien à la pêche et l’aquaculture"
            )


def test_export_pptx_d_un_champ_tableau(entreprise_factory, alice):
    entreprise = entreprise_factory(utilisateur=alice)
    rapport_vsme = RapportVSME.objects.create(entreprise=entreprise, annee=2026)
    indicateur = Indicateur(
        rapport_vsme=rapport_vsme,
        schema_id="B1-24-e-vii",  # Liste des sites
        data={
            "sites": [
                {
                    "id_site": 1,
                    "nom_site": "usine",
                    "adresse": "rue du secondaire",
                    "code_postal": "1028",
                    "ville": "Tirana",
                    "pays": "ALB",
                    "geolocalisation": "[1,2]",
                },
                {
                    "id_site": 2,
                    "nom_site": "bureaux",
                    "adresse": "rue du tertiaire",
                    "code_postal": "33000",
                    "ville": "Bordeaux",
                    "pays": "FRA",
                    "geolocalisation": "[3,4]",
                },
            ]
        },
    )
    chemin_pptx = Path(settings.BASE_DIR, "vsme/exports/vsme.pptx")
    presentation = Presentation(chemin_pptx)

    export_pptx_exigence_de_publication(
        EXIGENCES_DE_PUBLICATION["B1"], presentation, {"B1-24-e-vii": indicateur}
    )

    shapes = presentation.slides[6].shapes
    for shape in shapes:
        if shape.name == "B1-25":
            tableau = shape.table
            assert tableau.cell(1, 0).text == "1"
            assert tableau.cell(1, 1).text == "usine"
            assert tableau.cell(1, 2).text == "rue du secondaire"
            assert tableau.cell(1, 3).text == "1028"
            assert tableau.cell(1, 4).text == "Tirana"
            assert tableau.cell(1, 5).text == "ALBANIE"
            assert tableau.cell(1, 6).text == "[1,2]"
            assert tableau.cell(2, 0).text == "2"
            assert tableau.cell(2, 1).text == "bureaux"
            assert tableau.cell(2, 2).text == "rue du tertiaire"
            assert tableau.cell(2, 3).text == "33000"
            assert tableau.cell(2, 4).text == "Bordeaux"
            assert tableau.cell(2, 5).text == "FRANCE"
            assert tableau.cell(2, 6).text == "[3,4]"
