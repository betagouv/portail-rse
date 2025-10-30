from django.conf import settings
from django.urls import reverse


CONTENU_PDF = b"%PDF-1.4\n%\xd3\xeb\xe9\xe1\n1 0 obj\n<</Title (CharteEngagements"


# note : les rapports CSRD sont uniquement officiels désormais
# Alice est l'utilisateur propriétaire rattaché aux entreprises de test


def test_serveur_IA_envoie_l_etat_d_avancement_de_l_analyse_1(
    client, document, mailoutbox
):
    rapport_csrd = document.rapports_csrd.select_related("entreprise").first()

    client.post(
        f"/ESRS-predict/{document.id}/{rapport_csrd.id}",
        {
            "status": "processing",
        },
    )

    document.refresh_from_db()
    assert document.etat == "processing"
    assert len(mailoutbox) == 0


def test_serveur_IA_envoie_l_etat_d_avancement_de_l_analyse_2(
    client, document, mailoutbox, alice
):
    rapport_csrd = document.rapports_csrd.select_related("entreprise").first()

    client.post(
        f"/ESRS-predict/{document.id}/{rapport_csrd.id}",
        {
            "status": "error",
            "msg": "MESSAGE",
        },
    )

    document.refresh_from_db()

    assert document.etat == "error"
    assert document.message == "MESSAGE"
    assert len(mailoutbox) == 1

    mail = mailoutbox[0]

    assert mail.from_email == settings.DEFAULT_FROM_EMAIL
    assert list(mail.to) == [alice.email]
    assert mail.template_id == settings.BREVO_RESULTAT_ANALYSE_IA_TEMPLATE


def test_serveur_IA_envoie_le_resultat_de_l_analyse(
    client, document, mailoutbox, alice
):
    rapport_csrd = document.rapports_csrd.select_related("entreprise").first()
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

    response = client.post(
        f"/ESRS-predict/{document.id}/{rapport_csrd.id}",
        {
            "status": "success",
            "resultat_json": RESULTATS,
        },
    )

    document.refresh_from_db()
    assert document.etat == "success"
    assert document.resultat_json == RESULTATS

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


def test_envoie_resultat_ia_email_non_bloquant(client, document, mocker):
    mocker.patch(
        "reglementations.views.csrd.analyse_ia.envoie_resultat_ia_email",
        side_effect=Exception,
    )
    capture_exception_mock = mocker.patch("sentry_sdk.capture_exception")

    rapport_csrd = document.rapports_csrd.select_related("entreprise").first()

    RESULTATS = """{
  "ESRS E1": [
    {
      "PAGES": 1,
      "TEXTS": "A"
    }
  ]
  }"""

    response = client.post(
        f"/ESRS-predict/{document.id}/{rapport_csrd.id}",
        {
            "status": "success",
            "resultat_json": RESULTATS,
        },
    )

    document.refresh_from_db()
    assert document.etat == "success"
    assert document.resultat_json == RESULTATS

    capture_exception_mock.assert_called_once()
    args, _ = capture_exception_mock.call_args
    assert isinstance(args[0], Exception)
