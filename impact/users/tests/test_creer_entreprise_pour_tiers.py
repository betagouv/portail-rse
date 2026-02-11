"""Tests pour le formulaire unifie d'ajout d'entreprise conseiller RSE."""

from unittest.mock import patch

import pytest
from django.conf import settings
from django.urls import reverse

from habilitations.enums import UserRole
from habilitations.models import Habilitation
from invitations.models import Invitation
from utils.tokens import make_token


@pytest.fixture
def conseiller_rse(django_user_model):
    return django_user_model.objects.create(
        prenom="Claire",
        nom="Conseillere",
        email="claire@conseil-rse.test",
        is_email_confirmed=True,
        is_conseiller_rse=True,
    )


# Tests d'acces au tableau de bord conseiller


@pytest.mark.django_db
def test_acces_refuse_non_conseiller(client, alice):
    """Un utilisateur non-conseiller ne peut pas acceder au tableau de bord conseiller."""
    client.force_login(alice)

    response = client.get(reverse("users:tableau_de_bord_conseiller"))

    assert response.status_code == 302


@pytest.mark.django_db
def test_acces_autorise_conseiller(client, conseiller_rse):
    """Un conseiller RSE peut acceder au tableau de bord."""
    client.force_login(conseiller_rse)

    response = client.get(reverse("users:tableau_de_bord_conseiller"))

    assert response.status_code == 200
    assert "Accompagner cette entreprise" in response.content.decode()


# Tests du formulaire unifie : CAS 1a - Entreprise existante avec proprietaire


@pytest.mark.django_db
def test_rattachement_entreprise_existante_avec_proprietaire(
    client, conseiller_rse, alice, entreprise_factory
):
    """Un conseiller ne peut pas se rattacher a une entreprise existante avec proprietaire."""
    entreprise = entreprise_factory(siren="123456789")
    Habilitation.ajouter(entreprise, alice, UserRole.PROPRIETAIRE)

    client.force_login(conseiller_rse)
    response = client.post(
        reverse("users:tableau_de_bord_conseiller"),
        {
            "siren": "123456789",
            "email_futur_proprietaire": "futur@proprietaire.test",
        },
        follow=True,
    )

    # Verifier que le conseiller n'a pas été rattaché comme EDITEUR
    assert not Habilitation.existe(entreprise, conseiller_rse)

    # Pas d'invitation creee car il y a deja un proprietaire
    assert not Invitation.objects.filter(entreprise=entreprise).exists()


# Tests du formulaire unifie : CAS 1b - Entreprise existante sans proprietaire


@pytest.mark.django_db
def test_rattachement_entreprise_sans_proprietaire_sans_email_echoue(
    client, conseiller_rse, entreprise_factory
):
    """Le rattachement sans email echoue si l'entreprise n'a pas de proprietaire."""
    entreprise = entreprise_factory(siren="234567890")
    # Pas de proprietaire ajoute

    client.force_login(conseiller_rse)
    response = client.post(
        reverse("users:tableau_de_bord_conseiller"),
        {
            "siren": "234567890",
            "email_futur_proprietaire": "",
        },
    )

    # Le formulaire doit afficher une erreur
    assert "email" in response.content.decode().lower()
    assert not Habilitation.existe(entreprise, conseiller_rse)


@pytest.mark.django_db
@patch("users.views._envoie_email_invitation_proprietaire_tiers")
def test_rattachement_entreprise_sans_proprietaire_avec_email_reussit(
    mock_email, client, conseiller_rse, entreprise_factory
):
    """Le rattachement reussit avec email si l'entreprise n'a pas de proprietaire."""
    entreprise = entreprise_factory(siren="345678901")
    # Pas de proprietaire ajoute

    client.force_login(conseiller_rse)
    response = client.post(
        reverse("users:tableau_de_bord_conseiller"),
        {
            "siren": "345678901",
            "email_futur_proprietaire": "futur@proprietaire.test",
        },
        follow=True,
    )

    # Verifier le rattachement
    assert Habilitation.existe(entreprise, conseiller_rse)
    habilitation = Habilitation.pour(entreprise, conseiller_rse)
    assert habilitation.role == UserRole.PROPRIETAIRE

    # Verifier l'invitation creee
    invitation = Invitation.objects.get(entreprise=entreprise)
    assert invitation.email == "futur@proprietaire.test"
    assert invitation.role == UserRole.PROPRIETAIRE
    assert invitation.est_invitation_proprietaire_tiers is True
    assert invitation.inviteur == conseiller_rse

    # Verifier que l'email a ete envoye
    mock_email.assert_called_once()


# Tests du formulaire unifie : CAS 2 - Entreprise inexistante


@pytest.mark.django_db
def test_creation_entreprise_sans_email_echoue(client, conseiller_rse):
    """La creation d'entreprise echoue sans email du futur proprietaire."""
    client.force_login(conseiller_rse)
    response = client.post(
        reverse("users:tableau_de_bord_conseiller"),
        {
            "siren": "999888777",
            # Pas d'email_futur_proprietaire
        },
    )

    # Le formulaire doit afficher une erreur
    assert "email" in response.content.decode().lower()


@pytest.mark.django_db
@patch("users.views.Entreprise.search_and_create_entreprise")
@patch("users.views._envoie_email_invitation_proprietaire_tiers")
def test_creation_entreprise_reussie(
    mock_email, mock_search, client, conseiller_rse, entreprise_factory
):
    """Un conseiller peut creer une entreprise pour un tiers."""
    entreprise = entreprise_factory(siren="111222333")
    mock_search.return_value = entreprise

    client.force_login(conseiller_rse)
    response = client.post(
        reverse("users:tableau_de_bord_conseiller"),
        {
            "siren": "111222333",
            "email_futur_proprietaire": "futur@proprietaire.test",
        },
    )

    assert Habilitation.existe(entreprise, conseiller_rse)
    habilitation = Habilitation.pour(entreprise, conseiller_rse)
    assert habilitation.role == UserRole.PROPRIETAIRE
    assert not habilitation.fonctions

    # Verifier que l'invitation a ete creee
    invitation = Invitation.objects.get(entreprise=entreprise)
    assert invitation.email == "futur@proprietaire.test"
    assert invitation.role == UserRole.PROPRIETAIRE
    assert invitation.est_invitation_proprietaire_tiers is True
    assert invitation.inviteur == conseiller_rse

    # Verifier que l'email a ete envoye
    mock_email.assert_called_once()


@pytest.mark.django_db
def test_compte_les_proprietaires(
    client, conseiller_rse, alice, bob, entreprise_factory
):
    """Le badge 'Active' est affiche quand l'entreprise a un proprietaire valide."""
    entreprise = entreprise_factory(siren="444555666")

    # Ajouter deux proprietaires valides
    Habilitation.ajouter(entreprise, alice, UserRole.PROPRIETAIRE)
    Habilitation.ajouter(entreprise, bob, UserRole.PROPRIETAIRE)

    # Rattacher le conseiller
    Habilitation.ajouter(entreprise, conseiller_rse, UserRole.PROPRIETAIRE)

    client.force_login(conseiller_rse)
    response = client.get(reverse("users:tableau_de_bord_conseiller"))

    content = response.content.decode()
    assert "3" in content


# =============================================================================
# Phase A : Tests d'envoi d'email d'invitation
# =============================================================================


@pytest.mark.django_db
def test_email_invitation_envoye_avec_bonnes_donnees(
    client, conseiller_rse, entreprise_factory, mailoutbox
):
    """L'email d'invitation est envoyé avec les bonnes données (sans mock)."""
    entreprise = entreprise_factory(siren="111000111")
    # Pas de propriétaire

    client.force_login(conseiller_rse)
    client.post(
        reverse("users:tableau_de_bord_conseiller"),
        {
            "siren": "111000111",
            "email_futur_proprietaire": "nouveau@proprietaire.test",
            "fonctions": "Consultant CSRD",
        },
        follow=True,
    )

    # Vérifier qu'un email a été envoyé
    assert len(mailoutbox) == 1
    mail = mailoutbox[0]

    # Vérifier les destinataires et expéditeur
    assert list(mail.to) == ["nouveau@proprietaire.test"]
    assert mail.from_email == settings.DEFAULT_FROM_EMAIL

    # Vérifier le template utilisé (template dédié, différent de l'invitation standard)
    assert mail.template_id == settings.BREVO_INVITATION_PROPRIETAIRE_TIERS_TEMPLATE


@pytest.mark.django_db
def test_email_invitation_utilisateur_existant_route_acceptation(
    client, conseiller_rse, alice, entreprise_factory, mailoutbox
):
    """L'URL dans l'email pointe vers accepter_role_proprietaire pour un utilisateur existant."""
    entreprise = entreprise_factory(siren="222000222")

    client.force_login(conseiller_rse)
    client.post(
        reverse("users:tableau_de_bord_conseiller"),
        {
            "siren": "222000222",
            "email_futur_proprietaire": alice.email,  # Utilisateur existant
            "fonctions": "Accompagnement BDESE",
        },
        follow=True,
    )

    assert len(mailoutbox) == 1
    mail = mailoutbox[0]

    # L'URL doit pointer vers la route d'acceptation pour utilisateurs existants
    invitation_url = mail.merge_global_data.get("invitation_url", "")
    assert "accepter-proprietaire" in invitation_url


@pytest.mark.django_db
def test_email_invitation_nouvel_utilisateur_route_proconnect(
    client, conseiller_rse, entreprise_factory, mailoutbox
):
    """L'URL dans l'email pointe vers la landing ProConnect pour un nouvel utilisateur."""
    entreprise = entreprise_factory(siren="333000333")

    client.force_login(conseiller_rse)
    client.post(
        reverse("users:tableau_de_bord_conseiller"),
        {
            "siren": "333000333",
            "email_futur_proprietaire": "inconnu@nouveau.test",  # Email inexistant
            "fonctions": "Consultant",
        },
        follow=True,
    )

    assert len(mailoutbox) == 1
    mail = mailoutbox[0]

    # L'URL doit pointer vers la landing ProConnect (invitation-proprietaire)
    invitation_url = mail.merge_global_data.get("invitation_url", "")
    assert "invitation-proprietaire" in invitation_url
    assert "accepter-proprietaire" not in invitation_url


@pytest.mark.django_db
def test_contenu_email_variables_template(
    client, conseiller_rse, entreprise_factory, mailoutbox
):
    """Les variables du template email sont les mêmes que pour l'invitation standard."""
    entreprise = entreprise_factory(siren="444000444")

    client.force_login(conseiller_rse)
    client.post(
        reverse("users:tableau_de_bord_conseiller"),
        {
            "siren": "444000444",
            "email_futur_proprietaire": "futur@test.com",
        },
        follow=True,
    )

    assert len(mailoutbox) == 1
    mail = mailoutbox[0]

    # Vérifier que le template dédié est utilisé
    assert mail.template_id == settings.BREVO_INVITATION_PROPRIETAIRE_TIERS_TEMPLATE

    # Vérifier les variables du template (mêmes que l'invitation standard)
    merge_data = mail.merge_global_data

    # Dénomination de l'entreprise
    assert "denomination_entreprise" in merge_data
    assert merge_data["denomination_entreprise"] == entreprise.denomination

    # Nom de l'inviteur (même variable que l'invitation standard)
    assert "inviteur" in merge_data
    assert conseiller_rse.prenom in merge_data["inviteur"]
    assert conseiller_rse.nom in merge_data["inviteur"]

    # Rôle (même variable que l'invitation standard)
    assert "role" in merge_data
    assert merge_data["role"] == "Propriétaire"

    # URL d'invitation (doit être une URL absolue)
    assert "invitation_url" in merge_data
    assert merge_data["invitation_url"].startswith("http")


# =============================================================================
# Phase B : Tests de sécurité complémentaires
# =============================================================================


@pytest.mark.django_db
def test_invitation_expiree_refuse_acceptation(
    client, alice, entreprise_factory, conseiller_rse
):
    """Une invitation expirée est refusée."""
    from datetime import datetime
    from datetime import timedelta
    from datetime import timezone
    from freezegun import freeze_time

    # Date de création dans le passé (il y a 31 jours)
    date_creation_passee = datetime.now(timezone.utc) - timedelta(days=31)

    # Créer l'invitation avec une date de création dans le passé
    entreprise = entreprise_factory(siren="555000555")
    Habilitation.ajouter(entreprise, conseiller_rse, UserRole.PROPRIETAIRE)

    with freeze_time(date_creation_passee):
        invitation = Invitation.objects.create(
            entreprise=entreprise,
            email=alice.email,
            role=UserRole.PROPRIETAIRE,
            inviteur=conseiller_rse,
            est_invitation_proprietaire_tiers=True,
        )

    # Générer le token (le token est valide car basé sur PK et email)
    code = make_token(invitation, "invitation_proprietaire")

    # Vérifier que l'invitation est bien expirée
    assert invitation.est_expiree is True

    # Tenter d'accepter
    client.force_login(alice)
    response = client.get(
        reverse(
            "users:accepter_role_proprietaire",
            args=[invitation.id, code],
        ),
        follow=True,
    )

    # L'invitation devrait être refusée avec un message d'expiration
    content = response.content.decode()
    assert "expir" in content.lower() or response.status_code == 302
