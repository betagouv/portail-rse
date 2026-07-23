import pytest
from django.urls import reverse

from habilitations.enums import UserRole
from habilitations.models import Habilitation
from invitations.models import Invitation
from utils.tokens import make_token


@pytest.fixture
def utilisateur_invite(django_user_model):
    return django_user_model.objects.create(
        prenom="Pierre",
        nom="Proprietaire",
        email="pierre@entreprise.test",
        is_email_confirmed=True,
    )


@pytest.fixture(params=[UserRole.ADMINISTRATEUR, UserRole.CONTRIBUTEUR])
def invitation(request, entreprise_factory, conseiller_rse):
    entreprise = entreprise_factory(siren="123456789")
    Habilitation.ajouter(entreprise, conseiller_rse, UserRole.CONTRIBUTEUR)

    return Invitation.objects.create(
        entreprise=entreprise,
        email="pierre@entreprise.test",
        role=request.param,
        inviteur=conseiller_rse,
    )


@pytest.mark.django_db
def test_acceptation_cree_habilitation(client, utilisateur_invite, invitation):
    """L'acceptation cree une habilitation avec le bon rôle."""
    client.force_login(utilisateur_invite)
    code = make_token(invitation, "invitation")

    response = client.get(
        reverse(
            "users:accepter_invitation",
            args=[invitation.id, code],
        ),
        follow=True,
    )

    # Verifier que l'habilitation a ete creee
    assert Habilitation.existe(invitation.entreprise, utilisateur_invite)
    habilitation = Habilitation.pour(invitation.entreprise, utilisateur_invite)
    assert habilitation.role == invitation.role

    utilisateur_invite.refresh_from_db()
    assert utilisateur_invite.is_conseiller_rse is False

    # Verifier que l'invitation a ete acceptee
    invitation.refresh_from_db()
    assert invitation.date_acceptation is not None

    assert response.status_code == 200
    assert response.redirect_chain == [
        (reverse("reglementations:tableau_de_bord", kwargs={"siren": "123456789"}), 302)
    ]
    assert "Vous êtes maintenant ajouté à l'entreprise" in response.content.decode()


@pytest.mark.django_db
def test_token_invalide_refuse(client, utilisateur_invite, invitation):
    """Un token invalide est refuse."""
    client.force_login(utilisateur_invite)

    response = client.get(
        reverse(
            "users:accepter_invitation",
            args=[invitation.id, "invalid_token"],
        ),
        follow=True,
    )

    assert response.status_code == 200
    assert response.redirect_chain == [(reverse("erreur_terminale"), 302)]


@pytest.mark.django_db
def test_email_different_refuse(client, alice, invitation):
    """Un utilisateur avec un email different est refuse."""
    client.force_login(alice)  # alice a un email different
    code = make_token(invitation, "invitation")

    response = client.get(
        reverse(
            "users:accepter_invitation",
            args=[invitation.id, code],
        ),
        follow=True,
    )

    assert response.status_code == 200
    assert response.redirect_chain == [(reverse("erreur_terminale"), 302)]


@pytest.mark.django_db
def test_invitation_deja_acceptee_redirige(client, utilisateur_invite, invitation):
    """Une invitation deja acceptee redirige vers le tableau de bord."""
    # Accepter l'invitation
    invitation.accepter(utilisateur_invite)

    client.force_login(utilisateur_invite)
    code = make_token(invitation, "invitation")

    response = client.get(
        reverse(
            "users:accepter_invitation",
            args=[invitation.id, code],
        ),
        follow=True,
    )

    assert response.status_code == 200
    assert response.redirect_chain == [
        (reverse("reglementations:tableau_de_bord", kwargs={"siren": "123456789"}), 302)
    ]
    assert "déjà été acceptée" in response.content.decode()


@pytest.mark.django_db
def test_invitation_inexistante_erreur(client, utilisateur_invite):
    """Une invitation inexistante retourne une erreur."""
    client.force_login(utilisateur_invite)

    response = client.get(
        reverse(
            "users:accepter_invitation",
            args=[99999, "some_code"],
        ),
        follow=True,
    )

    assert response.status_code == 200
    assert response.redirect_chain == [(reverse("erreur_terminale"), 302)]
