from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from pytest_django.asserts import assertTemplateUsed

from analyseia.models import AnalyseIA

CONTENU_PDF = b"%PDF-1.4\n%\xd3\xeb\xe9\xe1\n1 0 obj\n<</Title (CharteEngagements"
ANALYSES_URL = "/analyses/{siren}/"
AJOUT_DOCUMENT_URL = ANALYSES_URL + "ajout_document/"
ANALYSE_BASE_URL = "/analyses/{analyse_id}/"
SUPPRESSION_DOCUMENT_URL = ANALYSE_BASE_URL + "suppression/"


def test_analyses_est_prive(client, entreprise_factory, alice):
    entreprise = entreprise_factory()

    url = ANALYSES_URL.format(siren=entreprise.siren)
    response = client.get(url)

    assert response.status_code == 302
    connexion_url = reverse("users:login")
    assert response.url == f"{connexion_url}?next={url}"

    client.force_login(alice)
    response = client.get(url)

    assert response.status_code == 403


def test_analyses_avec_utilisateur_authentifie(client, entreprise_factory, alice):
    entreprise = entreprise_factory(utilisateur=alice)
    client.force_login(alice)

    url = ANALYSES_URL.format(siren=entreprise.siren)
    response = client.get(url)

    assert response.status_code == 200
    assertTemplateUsed(response, "base.html")
    assertTemplateUsed(response, "snippets/tableau_de_bord_menu.html")
    assertTemplateUsed(response, "analyseia/accueil.html")
    assertTemplateUsed(response, "snippets/onglets_analyses.html")


def test_analyses_sans_siren(client, entreprise_factory, alice):
    entreprise = entreprise_factory(utilisateur=alice)
    client.force_login(alice)

    response = client.get("/analyses/", follow=True)

    assert response.status_code == 200
    assert response.redirect_chain == [
        (ANALYSES_URL.format(siren=entreprise.siren), 302)
    ]


def test_ajout_document_par_utilisateur_autorise(client, entreprise_factory, alice):
    entreprise = entreprise_factory(utilisateur=alice)
    client.force_login(alice)
    fichier = SimpleUploadedFile("test.pdf", CONTENU_PDF)

    url = AJOUT_DOCUMENT_URL.format(siren=entreprise.siren)
    response = client.post(
        url,
        {"fichier": fichier},
    )

    assert response.status_code == 302
    assert response.url == reverse(
        "analyseia:analyses",
        kwargs={
            "siren": entreprise.siren,
        },
    )
    assert entreprise.analyses_ia.count() == 1
    assert entreprise.analyses_ia.first().nom == "test.pdf"


def test_ajout_document_par_utilisateur_non_autorise(client, entreprise_factory, bob):
    entreprise = entreprise_factory()
    client.force_login(bob)
    fichier = SimpleUploadedFile("test.pdf", CONTENU_PDF)

    url = AJOUT_DOCUMENT_URL.format(siren=entreprise.siren)
    response = client.post(
        url,
        {"fichier": fichier},
    )

    assert response.status_code == 403
    assert entreprise.analyses_ia.count() == 0


def test_ajout_document_sur_entreprise_inexistante(client, alice):
    client.force_login(alice)
    fichier = SimpleUploadedFile("test.pdf", CONTENU_PDF)

    url = AJOUT_DOCUMENT_URL.format(siren="0000000000")
    response = client.post(
        url,
        {"fichier": fichier},
    )

    assert response.status_code == 404
    assert AnalyseIA.objects.count() == 0


def test_ajout_document_sans_extension_pdf(client, entreprise_factory, alice):
    entreprise = entreprise_factory(utilisateur=alice)
    client.force_login(alice)
    fichier = SimpleUploadedFile("test.odt", b"libre office writer data")

    url = AJOUT_DOCUMENT_URL.format(siren=entreprise.siren)
    response = client.post(
        url,
        {"fichier": fichier},
    )

    assert response.status_code == 400
    assert entreprise.analyses_ia.count() == 0


def test_ajout_document_dont_le_contenu_n_est_pas_du_pdf(
    client, entreprise_factory, alice
):
    entreprise = entreprise_factory(utilisateur=alice)
    client.force_login(alice)
    fichier = SimpleUploadedFile("test.pdf", b"pas un pdf")

    url = AJOUT_DOCUMENT_URL.format(siren=entreprise.siren)
    response = client.post(
        url,
        {"fichier": fichier},
    )

    assert response.status_code == 400
    assert entreprise.analyses_ia.count() == 0
