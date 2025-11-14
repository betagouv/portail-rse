from django.shortcuts import reverse

from habilitations.enums import UserRole
from habilitations.models import Habilitation
from invitations.models import Invitation
from users.models import User


def test_utilisateur_non_authentifie_ne_peut_pas_inviter(client, entreprise_factory):
    entreprise = entreprise_factory()
    data = {"email": "attacker@evil.com", "role": UserRole.PROPRIETAIRE}
    url = f"/invitation/{entreprise.siren}"

    response = client.post(url, data=data)

    assert response.status_code in [302, 403]
    assert Invitation.objects.filter(entreprise=entreprise).count() == 0
    assert Habilitation.objects.filter(entreprise=entreprise).count() == 0


def test_utilisateur_non_membre_ne_peut_pas_inviter_vers_entreprise_tierce(
    client, alice, entreprise_factory
):
    entreprise_cible = entreprise_factory()
    client.force_login(alice)

    data = {"email": alice.email, "role": UserRole.PROPRIETAIRE}
    url = f"/invitation/{entreprise_cible.siren}"

    response = client.post(url, data=data)

    assert response.status_code == 403
    assert not Habilitation.objects.filter(
        entreprise=entreprise_cible, user=alice
    ).exists()
    assert not Invitation.objects.filter(entreprise=entreprise_cible).exists()


def test_utilisateur_non_membre_ne_peut_pas_inviter_un_tiers(
    client, alice, bob, entreprise_factory
):
    entreprise_cible = entreprise_factory()
    client.force_login(alice)

    data = {"email": bob.email, "role": UserRole.PROPRIETAIRE}
    url = f"/invitation/{entreprise_cible.siren}"

    response = client.post(url, data=data)

    assert response.status_code == 403
    assert not Habilitation.objects.filter(
        entreprise=entreprise_cible, user=bob
    ).exists()
    assert not Invitation.objects.filter(entreprise=entreprise_cible).exists()


def test_editeur_ne_peut_pas_inviter(client, alice, bob, entreprise_factory):
    entreprise = entreprise_factory()
    Habilitation.ajouter(entreprise, alice, role=UserRole.EDITEUR)
    client.force_login(alice)

    data = {"email": bob.email, "role": UserRole.EDITEUR}
    url = f"/invitation/{entreprise.siren}"

    response = client.post(url, data=data)

    assert response.status_code == 403
    assert not Habilitation.objects.filter(entreprise=entreprise, user=bob).exists()
    assert (
        Invitation.objects.filter(entreprise=entreprise, email=bob.email).count() == 0
    )


def test_proprietaire_peut_inviter(client, alice, bob, entreprise_factory, mailoutbox):
    entreprise = entreprise_factory()
    Habilitation.ajouter(entreprise, alice, role=UserRole.PROPRIETAIRE)
    client.force_login(alice)

    # un simple login ne met pas l'entreprise courante en session
    client.get(
        reverse("reglementations:tableau_de_bord", kwargs={"siren": entreprise.siren})
    )

    data = {"email": bob.email, "role": UserRole.EDITEUR}
    url = f"/invitation/{entreprise.siren}"

    response = client.post(url, data=data, follow=True)

    assert response.status_code == 200
    assert Habilitation.objects.filter(entreprise=entreprise, user=bob).exists()
    assert Invitation.objects.filter(entreprise=entreprise, email=bob.email).exists()
    assert len(mailoutbox) == 1


def test_invitation_avec_siren_arbitraire(
    client, alice, entreprise_factory, entreprise_unique_factory
):
    entreprise_alice = entreprise_factory()
    Habilitation.ajouter(entreprise_alice, alice, role=UserRole.PROPRIETAIRE)

    entreprise_victime = entreprise_unique_factory()

    client.force_login(alice)

    data = {"email": alice.email, "role": UserRole.PROPRIETAIRE}
    url = f"/invitation/{entreprise_victime.siren}"

    response = client.post(url, data=data)

    assert response.status_code == 403
    assert (
        Habilitation.objects.filter(user=alice, entreprise=entreprise_victime).count()
        == 0
    )
    assert (
        Habilitation.objects.filter(user=alice, entreprise=entreprise_alice).count()
        == 1
    )


def test_attaque_avec_curl(client, alice, bob, entreprise_factory):
    entreprise_bob = entreprise_factory()
    Habilitation.ajouter(entreprise_bob, bob, role=UserRole.PROPRIETAIRE)

    client.force_login(alice)

    data = {
        "csrfmiddlewaretoken": "zDgWFRoFkVf8N7q03zKVEA8NLircTAQEOMakgzJZpCQQR5JjghKkkLGlTWZwFZev",
        "email": alice.email,
        "role": "proprietaire",
    }
    url = f"/invitation/{entreprise_bob.siren}"

    response = client.post(url, data=data)

    assert response.status_code == 403
    assert not Habilitation.objects.filter(
        entreprise=entreprise_bob, user=alice
    ).exists()
    habilitations = Habilitation.objects.filter(entreprise=entreprise_bob)
    assert habilitations.count() == 1
    assert habilitations.first().user == bob


def test_invitation_depuis_autre_entreprise(
    client, alice, bob, entreprise_factory, entreprise_unique_factory
):
    entreprise_alice = entreprise_factory()
    entreprise_bob = entreprise_unique_factory()

    Habilitation.ajouter(entreprise_alice, alice, role=UserRole.PROPRIETAIRE)
    Habilitation.ajouter(entreprise_bob, bob, role=UserRole.PROPRIETAIRE)

    client.force_login(alice)

    data = {"email": "complice@evil.com", "role": UserRole.PROPRIETAIRE}
    url = f"/invitation/{entreprise_bob.siren}"

    response = client.post(url, data=data)

    assert response.status_code == 403
    assert not Invitation.objects.filter(entreprise=entreprise_bob).exists()
    assert Habilitation.objects.filter(entreprise=entreprise_bob).count() == 1
    assert Habilitation.objects.filter(entreprise=entreprise_bob).first().user == bob


def test_attaque_reelle_avec_session_etablie(
    client, alice, bob, entreprise_unique_factory
):
    entreprise_alice = entreprise_unique_factory(siren="111111111")
    Habilitation.ajouter(entreprise_alice, alice, role=UserRole.PROPRIETAIRE)
    entreprise_bob = entreprise_unique_factory(siren="222222222")
    Habilitation.ajouter(entreprise_bob, bob, role=UserRole.PROPRIETAIRE)

    client.force_login(alice)
    response = client.get(
        reverse(
            "reglementations:tableau_de_bord", kwargs={"siren": entreprise_alice.siren}
        )
    )

    assert response.status_code == 200
    assert client.session.get("entreprise") == entreprise_alice.siren

    data = {"email": alice.email, "role": UserRole.PROPRIETAIRE}
    url = f"/invitation/{entreprise_bob.siren}"

    response = client.post(url, data=data)

    assert (
        response.status_code == 403
    ), "Alice ne doit pas pouvoir inviter vers l'entreprise de Bob"
    assert not Habilitation.objects.filter(
        entreprise=entreprise_bob, user=alice
    ).exists(), "Alice ne doit pas avoir d'habilitation sur l'entreprise de Bob"
    assert (
        Invitation.objects.filter(entreprise=entreprise_bob).count() == 0
    ), "Il ne doit pas y avoir d'invitation sur l'entreprise de Bob"


def test_attaque_gerer_habilitation_autre_entreprise(
    client, alice, bob, entreprise_unique_factory
):
    entreprise_alice = entreprise_unique_factory(siren="333333333")
    Habilitation.ajouter(entreprise_alice, alice, role=UserRole.PROPRIETAIRE)

    entreprise_bob = entreprise_unique_factory(siren="444444444")
    Habilitation.ajouter(entreprise_bob, bob, role=UserRole.PROPRIETAIRE)

    jane = User.objects.create(
        email="jane@portail-rse.test",
        prenom="Jane",
        nom="DeLaJungle",
        is_email_confirmed=True,
    )
    habilitation_jane = Habilitation.ajouter(
        entreprise_bob, jane, role=UserRole.EDITEUR
    )

    client.force_login(alice)
    response = client.get(
        reverse(
            "reglementations:tableau_de_bord", kwargs={"siren": entreprise_alice.siren}
        )
    )
    assert response.status_code == 200
    assert client.session.get("entreprise") == entreprise_alice.siren

    response = client.post(
        f"/habilitation/{habilitation_jane.id}",
        data={"role": UserRole.PROPRIETAIRE},
        content_type="application/x-www-form-urlencoded",
    )

    habilitation_jane.refresh_from_db()
    assert (
        response.status_code == 403
    ), "Alice ne doit pas pouvoir modifier l'habilitation de Jane"
    assert (
        habilitation_jane.role == UserRole.EDITEUR.value
    ), "Le rôle de Jane ne doit pas changer"

    response = client.delete(f"/habilitation/{habilitation_jane.id}")

    # Vérifier que l'attaque a été bloquée
    assert (
        response.status_code == 403
    ), "Alice ne doit pas pouvoir supprimer l'habilitation de Jane"
    assert Habilitation.objects.filter(
        pk=habilitation_jane.id
    ).exists(), "L'habilitation de Jane ne doit pas être supprimée"
