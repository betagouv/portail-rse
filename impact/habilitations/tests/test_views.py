import html

import pytest
from django.conf import settings
from django.urls import reverse

from habilitations.enums import UserRole
from habilitations.models import Habilitation
from invitations.models import Invitation


def test_une_invitation_a_devenir_membre_pour_un_compte_existant_est_activée_directement(
    client, alice, bob, entreprise_factory, mailoutbox
):
    entreprise = entreprise_factory()
    Habilitation.ajouter(entreprise, alice, fonctions="Présidente")
    client.force_login(alice)
    data = {"email": bob.email, "role": UserRole.PROPRIETAIRE}
    url = f"/invitation/{entreprise.siren}"
    redirect_url = reverse("reglementations:tableau_de_bord", args=[entreprise.siren])

    # un simple login ne met pas l'entreprise courante en session
    client.get(redirect_url)

    response = client.post(url, data=data, follow=True)

    invitation = Invitation.objects.get(entreprise=entreprise, email=bob.email)
    assert invitation.role == UserRole.PROPRIETAIRE.value
    assert invitation.inviteur == alice
    assert invitation.date_acceptation
    assert Habilitation.objects.filter(
        entreprise=entreprise, user=bob, invitation=invitation
    ).first()
    assert response.redirect_chain == [(redirect_url, 302)]
    content = html.unescape(response.content.decode("utf-8"))
    assert "L'utilisateur a été ajouté." in content
    assert len(mailoutbox) == 1
    mail = mailoutbox[0]
    assert mail.from_email == settings.DEFAULT_FROM_EMAIL
    assert list(mail.to) == [bob.email]
    assert mail.template_id == settings.BREVO_AJOUT_MEMBRE_TEMPLATE


def test_succès_invitation_a_devenir_membre(
    client, alice, entreprise_factory, mailoutbox
):
    entreprise = entreprise_factory()
    Habilitation.ajouter(entreprise, alice, fonctions="Présidente")
    client.force_login(alice)
    EMAIL_INVITE = "bob@bob.test"
    data = {"email": EMAIL_INVITE, "role": UserRole.EDITEUR}
    url = f"/invitation/{entreprise.siren}"
    redirect_url = reverse("reglementations:tableau_de_bord", args=[entreprise.siren])

    # un simple login ne met pas l'entreprise courante en session
    client.get(redirect_url)

    response = client.post(url, data=data, follow=True)

    invitations = Invitation.objects.filter(entreprise=entreprise, email=EMAIL_INVITE)
    assert len(invitations) == 1
    invitation = invitations[0]
    assert invitation.role == "editeur"
    assert invitation.inviteur == alice
    assert response.redirect_chain == [(redirect_url, 302)]
    content = html.unescape(response.content.decode("utf-8"))
    assert "L'invitation a été envoyée." in content
    assert len(mailoutbox) == 1
    mail = mailoutbox[0]
    assert mail.from_email == settings.DEFAULT_FROM_EMAIL
    assert list(mail.to) == [EMAIL_INVITE]
    assert mail.template_id == settings.BREVO_INVITATION_TEMPLATE


def test_erreur_invitation_a_devenir_membre_car_email_incorrect(
    client, alice, entreprise_factory, mailoutbox
):
    entreprise = entreprise_factory()
    Habilitation.ajouter(entreprise, alice, fonctions="Présidente")

    client.force_login(alice)
    client.get(reverse("reglementations:tableau_de_bord", args=[entreprise.siren]))

    EMAIL_INVITE = "bob"
    data = {
        "email": EMAIL_INVITE,
    }
    url = f"/invitation/{entreprise.siren}"

    response = client.post(url, data=data, follow=True)

    invitations = Invitation.objects.filter(entreprise=entreprise, email=EMAIL_INVITE)
    assert len(invitations) == 0
    assert len(mailoutbox) == 0
    assert response.status_code == 200
    content = html.unescape(response.content.decode("utf-8"))
    assert "L'invitation a échoué car le formulaire contient des erreurs." in content


@pytest.mark.django_db(transaction=True)
def test_erreur_invitation_a_devenir_membre_car_deja_membre(
    client, alice, bob, entreprise_factory, mailoutbox
):
    entreprise = entreprise_factory()
    Habilitation.ajouter(entreprise, alice, fonctions="Présidente")
    Habilitation.ajouter(entreprise, bob, fonctions="Vice-président")

    client.force_login(alice)
    client.get(reverse("reglementations:tableau_de_bord", args=[entreprise.siren]))

    data = {"email": bob.email, "role": UserRole.EDITEUR}
    url = f"/invitation/{entreprise.siren}"

    response = client.post(url, data=data, follow=True)

    assert response.status_code == 200
    content = html.unescape(response.content.decode("utf-8"))
    assert (
        "L'invitation a échoué car cette personne est déjà membre de l'entreprise."
        in content
    )


def test_acces_vues_actions(client, entreprise_factory, alice, bob):
    # les vues traitant les actions d'habilitation doivent être accessibles aux propriétaires uniquement
    entreprise = entreprise_factory()
    h1 = Habilitation.ajouter(entreprise, bob, role=UserRole.PROPRIETAIRE)
    h2 = Habilitation.ajouter(entreprise, alice, role=UserRole.EDITEUR)

    # La session doit être affectée à une variable pour être utilisable
    # https://docs.djangoproject.com/en/5.2/topics/testing/tools/#django.test.Client.session
    session = client.session
    session["entreprise"] = entreprise.siren
    session.save()

    # alice ne peut pas accéder aux fonctions de vue pour l'habilitation
    client.force_login(alice)
    response = client.post(
        reverse("habilitations:gerer_habilitation", kwargs={"id": h1.pk}),
        data={"role": UserRole.PROPRIETAIRE},
    )
    assert (
        response.status_code == 403
    ), "Cet accès (POST/modification) ne doit pas être autorisé pour Alice"

    response = client.delete(
        reverse("habilitations:gerer_habilitation", kwargs={"id": h1.pk})
    )
    assert (
        response.status_code == 403
    ), "Cet accès (DELETE/suppression) ne doit pas être autorisé pour Alice"

    # bob est propriétaire : il doit pouvoir tout faire
    client.force_login(bob)
    session = client.session
    session["entreprise"] = entreprise.siren
    session.save()

    response = client.get(
        reverse("habilitations:gerer_habilitation", kwargs={"id": h1.pk})
    )
    assert (
        response.status_code == 405
    ), "Le type de méthode doit être filtré (POST et DELETE uniquement)"

    response = client.post(
        reverse("habilitations:gerer_habilitation", kwargs={"id": h2.pk}),
        data={"role": UserRole.PROPRIETAIRE},
    )
    assert (
        response.status_code == 303
    ), "Le type de méthode doit être une redirection (303)"
    assert UserRole.PROPRIETAIRE == Habilitation.role_pour(entreprise, alice)

    response = client.delete(
        reverse("habilitations:gerer_habilitation", kwargs={"id": h2.pk})
    )
    assert (
        response.status_code == 303
    ), "Le type de méthode doit être une redirection (303)"
    with pytest.raises(Habilitation.DoesNotExist):
        Habilitation.role_pour(entreprise, alice)


def test_auto_modification(client, entreprise_factory, bob):
    # un utilisateur ne peut pas modifier ses habilitations
    entreprise = entreprise_factory()
    habilitation = Habilitation.ajouter(entreprise, bob, role=UserRole.PROPRIETAIRE)
    session = client.session
    session["entreprise"] = entreprise.siren
    session.save()

    client.force_login(bob)
    response = client.delete(
        reverse("habilitations:gerer_habilitation", kwargs={"id": habilitation.pk})
    )
    assert response.status_code == 400, "Bob ne peut pas modifier ses habilitations"
