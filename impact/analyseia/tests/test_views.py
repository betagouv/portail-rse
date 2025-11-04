from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from pytest_django.asserts import assertTemplateUsed

from analyseia.models import AnalyseIA
from api.exceptions import APIError

CONTENU_PDF = b"%PDF-1.4\n%\xd3\xeb\xe9\xe1\n1 0 obj\n<</Title (CharteEngagements"
ANALYSES_URL = "/analyses/{siren}/"
AJOUT_DOCUMENT_URL = ANALYSES_URL + "ajout_document/"
AJOUT_DOCUMENT_LIE_CSRD_URL = ANALYSES_URL + "ajout_document/{csrd_id}"
ANALYSE_BASE_URL = "/analyses/{analyse_id}/"
SUPPRESSION_ANALYSE_URL = ANALYSE_BASE_URL + "suppression/"
LANCEMENT_ANALYSE_URL = ANALYSE_BASE_URL + "lancement_analyse/"
ACTUALISATION_ETAT_URL = ANALYSE_BASE_URL + "etat/"
CSRD_ANALYSE_ECART_URL = "/csrd/{siren}/etape-analyse-ecart"


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


def test_ajout_document_liée_à_une_entreprise_par_utilisateur_autorise(
    client, entreprise_factory, alice
):
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


def test_ajout_document_liée_à_un_rapport_csrd_par_utilisateur_autorise(
    client, csrd, alice
):
    entreprise = csrd.entreprise
    client.force_login(alice)
    fichier = SimpleUploadedFile("test.pdf", CONTENU_PDF)

    url = AJOUT_DOCUMENT_LIE_CSRD_URL.format(siren=entreprise.siren, csrd_id=csrd.id)
    response = client.post(
        url,
        {"fichier": fichier},
    )

    assert response.status_code == 302
    assert response.url == reverse(
        "reglementations:gestion_csrd",
        kwargs={
            "siren": csrd.entreprise.siren,
            "id_etape": "analyse-ecart",
        },
    )
    assert csrd.analyses_ia.count() == 1
    assert csrd.analyses_ia.first().nom == "test.pdf"


def test_ajout_document_liée_à_une_entreprise_par_utilisateur_non_autorise(
    client, entreprise_factory, bob
):
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


def test_ajout_document_liée_à_un_rapport_csrd_par_utilisateur_non_autorise(
    client, csrd, bob
):
    entreprise = csrd.entreprise
    client.force_login(bob)
    fichier = SimpleUploadedFile("test.pdf", CONTENU_PDF)

    url = AJOUT_DOCUMENT_LIE_CSRD_URL.format(siren=entreprise.siren, csrd_id=csrd.id)
    response = client.post(
        url,
        {"fichier": fichier},
    )

    assert response.status_code == 403
    assert csrd.analyses_ia.count() == 0


def test_ajout_document_liée_à_une_entreprise_inexistante(client, alice):
    client.force_login(alice)
    fichier = SimpleUploadedFile("test.pdf", CONTENU_PDF)

    url = AJOUT_DOCUMENT_URL.format(siren="0000000000")
    response = client.post(
        url,
        {"fichier": fichier},
    )

    assert response.status_code == 404
    assert AnalyseIA.objects.count() == 0


def test_ajout_document_liée_à_un_rapport_csrd_inexistant(
    client, entreprise_factory, alice
):
    entreprise = entreprise_factory(utilisateur=alice)
    client.force_login(alice)
    fichier = SimpleUploadedFile("test.pdf", CONTENU_PDF)

    url = AJOUT_DOCUMENT_LIE_CSRD_URL.format(siren=entreprise.siren, csrd_id=42)
    response = client.post(
        url,
        {"fichier": fichier},
    )

    assert response.status_code == 404
    assert AnalyseIA.objects.count() == 0


def test_ajout_document_liée_à_une_entreprise_sans_extension_pdf(
    client, entreprise_factory, alice
):
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


def test_ajout_document_liée_à_un_rapport_csrd_sans_extension_pdf(client, csrd, alice):
    entreprise = csrd.entreprise
    client.force_login(alice)
    fichier = SimpleUploadedFile("test.odt", b"libre office writer data")

    url = AJOUT_DOCUMENT_LIE_CSRD_URL.format(siren=entreprise.siren, csrd_id=csrd.id)
    response = client.post(
        url,
        {"fichier": fichier},
    )

    assert response.status_code == 400
    assert csrd.analyses_ia.count() == 0


def test_ajout_document_liée_à_une_entreprise__dont_le_contenu_n_est_pas_du_pdf(
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


def test_ajout_document_liée_à_un_rapport_csrd_dont_le_contenu_n_est_pas_du_pdf(
    client, csrd, alice
):
    entreprise = csrd.entreprise
    client.force_login(alice)
    fichier = SimpleUploadedFile("test.pdf", b"pas un pdf")

    url = AJOUT_DOCUMENT_LIE_CSRD_URL.format(siren=entreprise.siren, csrd_id=csrd.id)
    response = client.post(
        url,
        {"fichier": fichier},
    )

    assert response.status_code == 400
    assert csrd.analyses_ia.count() == 0


def test_suppression_analyse_liée_à_une_entreprise_par_utilisateur_autorise(
    client, analyse, alice
):
    entreprise = analyse.entreprise
    client.force_login(alice)

    url = SUPPRESSION_ANALYSE_URL.format(analyse_id=analyse.id)
    response = client.post(url)

    assert response.status_code == 302
    assert response.url == reverse(
        "analyseia:analyses",
        kwargs={
            "siren": entreprise.siren,
        },
    )
    assert AnalyseIA.objects.count() == 0


def test_suppression_analyse_liée_à_un_rapport_csrd_par_utilisateur_autorise(
    client, analyse_avec_csrd, alice
):
    client.force_login(alice)
    csrd = analyse_avec_csrd.rapports_csrd.first()
    entreprise = csrd.entreprise

    url = SUPPRESSION_ANALYSE_URL.format(analyse_id=analyse_avec_csrd.id)
    response = client.post(url)

    assert response.status_code == 302
    assert response.url == reverse(
        "reglementations:gestion_csrd",
        kwargs={
            "siren": entreprise.siren,
            "id_etape": "analyse-ecart",
        },
    )
    assert AnalyseIA.objects.count() == 0


def test_suppression_analyse_par_utilisateur_non_autorise(client, analyse, bob):
    client.force_login(bob)

    url = SUPPRESSION_ANALYSE_URL.format(analyse_id=analyse.id)
    response = client.post(url)

    assert response.status_code == 403
    assert AnalyseIA.objects.count() == 1


def test_suppression_analyse_inexistante(client, analyse, alice):
    client.force_login(alice)

    url = SUPPRESSION_ANALYSE_URL.format(analyse_id=42)
    response = client.post(url)

    assert response.status_code == 404
    assert AnalyseIA.objects.count() == 1


def test_lancement_d_analyse_IA_liée_à_une_entreprise_par_utilisateur_autorise(
    client, mock_api_analyse_ia, analyse, alice
):
    client.force_login(alice)

    url = LANCEMENT_ANALYSE_URL.format(analyse_id=analyse.id)
    response = client.post(url, follow=True)

    callback_url = response.wsgi_request.build_absolute_uri(
        reverse(
            "analyseia:actualisation_etat",
            kwargs={
                "id_analyse": analyse.id,
            },
        )
    )

    mock_api_analyse_ia.assert_called_once_with(
        analyse.id, analyse.fichier.url, callback_url
    )
    analyse.refresh_from_db()
    assert analyse.etat == "pending"
    assert response.status_code == 200
    assert "L'analyse a bien été lancée." in response.content.decode("utf-8")
    assert response.redirect_chain == [
        (ANALYSES_URL.format(siren=analyse.entreprise.siren), 302)
    ]


def test_lancement_d_analyse_IA_liée_à_un_rapport_csrd_par_utilisateur_autorise(
    client, mock_api_analyse_ia, analyse_avec_csrd, alice
):
    analyse = analyse_avec_csrd
    csrd = analyse.rapports_csrd.first()
    client.force_login(alice)

    url = LANCEMENT_ANALYSE_URL.format(analyse_id=analyse.id)
    response = client.post(url, follow=True)

    callback_url = response.wsgi_request.build_absolute_uri(
        reverse(
            "analyseia:actualisation_etat",
            kwargs={
                "id_analyse": analyse.id,
            },
        )
    )

    mock_api_analyse_ia.assert_called_once_with(
        analyse.id, analyse.fichier.url, callback_url
    )
    analyse.refresh_from_db()
    assert analyse.etat == "pending"
    assert response.status_code == 200
    assert "L'analyse a bien été lancée." in response.content.decode("utf-8")
    assert response.redirect_chain == [
        (CSRD_ANALYSE_ECART_URL.format(siren=csrd.entreprise.siren), 302)
    ]


def test_lancement_d_analyse_IA_par_utilisateur_non_autorise(
    client, mock_api_analyse_ia, analyse, bob
):
    client.force_login(bob)

    url = LANCEMENT_ANALYSE_URL.format(analyse_id=analyse.id)
    response = client.post(
        url,
    )

    assert response.status_code == 403
    assert not analyse.etat
    assert not mock_api_analyse_ia.called


def test_lancement_d_analyse_IA_redirige_vers_la_connexion_si_non_connecté(
    client, mock_api_analyse_ia, analyse
):
    url = LANCEMENT_ANALYSE_URL.format(analyse_id=analyse.id)
    response = client.post(url)

    assert response.status_code == 302
    assert not analyse.etat
    assert not mock_api_analyse_ia.called


def test_lancement_d_analyse_IA_erreur_API(client, mock_api_analyse_ia, analyse, alice):
    message_erreur = (
        "Le service est actuellement indisponible. Merci de réessayer plus tard."
    )
    mock_api_analyse_ia.side_effect = APIError(message_erreur)
    client.force_login(alice)

    url = LANCEMENT_ANALYSE_URL.format(analyse_id=analyse.id)
    response = client.post(url, follow=True)

    analyse.refresh_from_db()
    assert not analyse.etat
    content = response.content.decode("utf-8")
    assert message_erreur in content


def test_serveur_IA_envoie_l_etat_d_avancement_de_l_analyse_1(
    client, analyse, mailoutbox
):
    url = ACTUALISATION_ETAT_URL.format(analyse_id=analyse.id)
    client.post(
        url,
        {
            "status": "processing",
        },
    )

    analyse.refresh_from_db()
    assert analyse.etat == "processing"
    assert len(mailoutbox) == 0


def test_serveur_IA_envoie_l_etat_d_avancement_de_l_analyse_2(
    client, analyse, mailoutbox, alice
):
    url = ACTUALISATION_ETAT_URL.format(analyse_id=analyse.id)
    client.post(
        url,
        {
            "status": "error",
            "msg": "MESSAGE",
        },
    )

    analyse.refresh_from_db()
    assert analyse.etat == "error"
    assert analyse.message == "MESSAGE"
    assert len(mailoutbox) == 1
    mail = mailoutbox[0]
    assert mail.from_email == settings.DEFAULT_FROM_EMAIL
    assert list(mail.to) == [alice.email]
    assert mail.template_id == settings.BREVO_RESULTAT_ANALYSE_IA_TEMPLATE


def test_serveur_IA_envoie_le_resultat_de_l_analyse_liée_à_une_entreprise(
    client, analyse, mailoutbox, alice
):
    RESULTATS = """{
  "ESRS E1": [
    {
      "PAGES": 1,
      "TEXTS": "A"
    }
  ],
  "ESRS E2": [
    {
      "PAGES": 6,
      "TEXTS": "B"
    },
    {
      "PAGES": 7,
      "TEXTS": "C"
    }
  ]
  }"""

    url = ACTUALISATION_ETAT_URL.format(analyse_id=analyse.id)
    response = client.post(
        url,
        {
            "status": "success",
            "resultat_json": RESULTATS,
        },
    )

    analyse.refresh_from_db()
    assert analyse.etat == "success"
    assert analyse.resultat_json == RESULTATS

    assert len(mailoutbox) == 1
    mail = mailoutbox[0]
    assert mail.from_email == settings.DEFAULT_FROM_EMAIL
    assert list(mail.to) == [alice.email]
    assert mail.template_id == settings.BREVO_RESULTAT_ANALYSE_IA_TEMPLATE
    assert mail.merge_global_data == {
        "resultat_ia_url": response.wsgi_request.build_absolute_uri(
            reverse(
                "analyseia:analyses",
                kwargs={
                    "siren": analyse.entreprise.siren,
                },
            )
        )
        + "#onglets"
    }


def test_serveur_IA_envoie_le_resultat_de_l_analyse_liée_à_un_rapport_csrd(
    client, analyse_avec_csrd, mailoutbox, alice
):
    analyse = analyse_avec_csrd
    rapport_csrd = analyse.rapports_csrd.first()
    RESULTATS = """{
  "ESRS E1": [
    {
      "PAGES": 1,
      "TEXTS": "A"
    }
  ],
  "ESRS E2": [
    {
      "PAGES": 6,
      "TEXTS": "B"
    },
    {
      "PAGES": 7,
      "TEXTS": "C"
    }
  ]
  }"""

    url = ACTUALISATION_ETAT_URL.format(analyse_id=analyse.id)
    response = client.post(
        url,
        {
            "status": "success",
            "resultat_json": RESULTATS,
        },
    )

    analyse.refresh_from_db()
    assert analyse.etat == "success"
    assert analyse.resultat_json == RESULTATS

    assert len(mailoutbox) == 1
    mail = mailoutbox[0]
    assert mail.from_email == settings.DEFAULT_FROM_EMAIL
    assert list(mail.to) == [alice.email]
    assert mail.template_id == settings.BREVO_RESULTAT_ANALYSE_IA_TEMPLATE
    assert mail.merge_global_data == {
        "resultat_ia_url": response.wsgi_request.build_absolute_uri(
            reverse(
                "reglementations:gestion_csrd",
                kwargs={
                    "siren": rapport_csrd.entreprise.siren,
                    "id_etape": "analyse-ecart",
                },
            )
        )
        + "#onglets"
    }


def test_envoie_resultat_ia_email_non_bloquant(client, analyse, mocker):
    mocker.patch(
        "analyseia.views._envoie_resultat_ia_email",
        side_effect=Exception,
    )
    capture_exception_mock = mocker.patch("sentry_sdk.capture_exception")

    RESULTATS = """{
  "ESRS E1": [
    {
      "PAGES": 1,
      "TEXTS": "A"
    }
  ]
  }"""

    url = ACTUALISATION_ETAT_URL.format(analyse_id=analyse.id)
    response = client.post(
        url,
        {
            "status": "success",
            "resultat_json": RESULTATS,
        },
    )

    analyse.refresh_from_db()
    assert analyse.etat == "success"
    assert analyse.resultat_json == RESULTATS

    capture_exception_mock.assert_called_once()
    args, _ = capture_exception_mock.call_args
    assert isinstance(args[0], Exception)
