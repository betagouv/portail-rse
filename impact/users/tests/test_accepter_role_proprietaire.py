import pytest
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


@pytest.fixture
def futur_proprietaire(django_user_model):
    return django_user_model.objects.create(
        prenom="Pierre",
        nom="Proprietaire",
        email="pierre@entreprise.test",
        is_email_confirmed=True,
    )


@pytest.fixture
def invitation_proprietaire_tiers(entreprise_factory, conseiller_rse):
    entreprise = entreprise_factory(siren="123456789")
    Habilitation.ajouter(entreprise, conseiller_rse, UserRole.EDITEUR)

    return Invitation.objects.create(
        entreprise=entreprise,
        email="pierre@entreprise.test",
        role=UserRole.PROPRIETAIRE,
        inviteur=conseiller_rse,
        est_invitation_proprietaire_tiers=True,
    )


@pytest.mark.django_db
def test_acces_page_acceptation_avec_token_valide(
    client, futur_proprietaire, invitation_proprietaire_tiers
):
    """Un utilisateur peut acceder a la page d'acceptation avec un token valide."""
    client.force_login(futur_proprietaire)
    code = make_token(invitation_proprietaire_tiers, "invitation_proprietaire")

    response = client.get(
        reverse(
            "users:accepter_role_proprietaire",
            args=[invitation_proprietaire_tiers.id, code],
        )
    )

    assert response.status_code == 200
    assert "Accepter le rôle de propriétaire" in response.content.decode()


@pytest.mark.django_db
def test_acceptation_cree_habilitation_proprietaire(
    client, futur_proprietaire, invitation_proprietaire_tiers
):
    """L'acceptation cree une habilitation PROPRIETAIRE."""
    client.force_login(futur_proprietaire)
    code = make_token(invitation_proprietaire_tiers, "invitation_proprietaire")

    response = client.post(
        reverse(
            "users:accepter_role_proprietaire",
            args=[invitation_proprietaire_tiers.id, code],
        )
    )

    # Verifier que l'habilitation a ete creee
    assert Habilitation.existe(
        invitation_proprietaire_tiers.entreprise, futur_proprietaire
    )
    habilitation = Habilitation.pour(
        invitation_proprietaire_tiers.entreprise, futur_proprietaire
    )
    assert habilitation.role == UserRole.PROPRIETAIRE

    # Verifier que l'invitation a ete acceptee
    invitation_proprietaire_tiers.refresh_from_db()
    assert invitation_proprietaire_tiers.date_acceptation is not None


@pytest.mark.django_db
def test_structure_plus_vacante_apres_acceptation(
    client, futur_proprietaire, invitation_proprietaire_tiers
):
    """L'entreprise n'est plus vacante apres acceptation."""
    entreprise = invitation_proprietaire_tiers.entreprise

    # Verifier qu'elle est vacante avant
    assert entreprise.est_structure_vacante is True

    client.force_login(futur_proprietaire)
    code = make_token(invitation_proprietaire_tiers, "invitation_proprietaire")

    client.post(
        reverse(
            "users:accepter_role_proprietaire",
            args=[invitation_proprietaire_tiers.id, code],
        )
    )

    # Verifier qu'elle n'est plus vacante apres
    entreprise.refresh_from_db()
    assert entreprise.est_structure_vacante is False


@pytest.mark.django_db
def test_token_invalide_refuse(
    client, futur_proprietaire, invitation_proprietaire_tiers
):
    """Un token invalide est refuse."""
    client.force_login(futur_proprietaire)

    response = client.get(
        reverse(
            "users:accepter_role_proprietaire",
            args=[invitation_proprietaire_tiers.id, "invalid_token"],
        )
    )

    assert response.status_code == 302


@pytest.mark.django_db
def test_email_different_refuse(client, alice, invitation_proprietaire_tiers):
    """Un utilisateur avec un email different est refuse."""
    client.force_login(alice)  # alice a un email different
    code = make_token(invitation_proprietaire_tiers, "invitation_proprietaire")

    response = client.get(
        reverse(
            "users:accepter_role_proprietaire",
            args=[invitation_proprietaire_tiers.id, code],
        )
    )

    assert response.status_code == 302


@pytest.mark.django_db
def test_invitation_deja_acceptee_redirige(
    client, futur_proprietaire, invitation_proprietaire_tiers
):
    """Une invitation deja acceptee redirige vers le tableau de bord."""
    # Accepter l'invitation
    invitation_proprietaire_tiers.accepter(futur_proprietaire)

    client.force_login(futur_proprietaire)
    code = make_token(invitation_proprietaire_tiers, "invitation_proprietaire")

    response = client.get(
        reverse(
            "users:accepter_role_proprietaire",
            args=[invitation_proprietaire_tiers.id, code],
        ),
        follow=True,
    )

    assert "déjà été acceptée" in response.content.decode()


@pytest.mark.django_db
def test_invitation_inexistante_erreur(client, futur_proprietaire):
    """Une invitation inexistante retourne une erreur."""
    client.force_login(futur_proprietaire)

    response = client.get(
        reverse(
            "users:accepter_role_proprietaire",
            args=[99999, "some_code"],
        )
    )

    assert response.status_code == 302
