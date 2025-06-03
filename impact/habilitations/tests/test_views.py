import html

from django.conf import settings
from django.urls import reverse
from pytest_django.asserts import assertTemplateUsed

from habilitations.models import Habilitation
from invitations.models import Invitation


def test_page_membres_d_une_entreprise(client, alice, bob, entreprise_factory):
    entreprise = entreprise_factory()
    Habilitation.ajouter(entreprise, bob, fonctions="Présidente")
    Habilitation.ajouter(entreprise, alice, fonctions="Présidente")
    client.force_login(alice)

    response = client.get(f"/droits/{entreprise.siren}")

    assertTemplateUsed(response, "habilitations/membres.html")
    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert alice.email in content


def test_page_membres_d_une_entreprise_nécessite_d_être_connecté(
    client, alice, entreprise_factory
):
    entreprise = entreprise_factory()
    Habilitation.ajouter(entreprise, alice, fonctions="Présidente")
    url = f"/droits/{entreprise.siren}"

    response = client.get(url, follow=True)

    redirect_url = f"""{reverse("users:login")}?next={url}"""
    assert response.redirect_chain == [(redirect_url, 302)]


def test_page_membres_d_une_entreprise_n_affiche_pas_les_utilisateurs_non_confirmés(
    client, alice, bob, entreprise_factory
):
    entreprise = entreprise_factory()
    bob.is_email_confirmed = False
    bob.save()
    Habilitation.ajouter(entreprise, bob, fonctions="Présidente")
    Habilitation.ajouter(entreprise, alice, fonctions="Présidente")
    client.force_login(alice)

    response = client.get(f"/droits/{entreprise.siren}")

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert bob.email not in content


def test_une_invitation_a_devenir_membre_pour_un_compte_existant_est_activée_directement(
    client, alice, bob, entreprise_factory, mailoutbox
):
    entreprise = entreprise_factory()
    Habilitation.ajouter(entreprise, alice, fonctions="Présidente")
    client.force_login(alice)
    data = {
        "email": bob.email,
    }
    url = f"/droits/{entreprise.siren}"

    response = client.post(url, data=data, follow=True)

    redirect_url = (
        f"""{reverse("habilitations:membres_entreprise", args=[entreprise.siren])}"""
    )
    assert (
        Invitation.objects.filter(entreprise=entreprise, email=bob.email).count() == 0
    )
    assert Habilitation.objects.filter(entreprise=entreprise, user=bob).first()
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
    data = {
        "email": EMAIL_INVITE,
    }
    url = f"/droits/{entreprise.siren}"

    response = client.post(url, data=data, follow=True)

    redirect_url = (
        f"""{reverse("habilitations:membres_entreprise", args=[entreprise.siren])}"""
    )
    invitations = Invitation.objects.filter(entreprise=entreprise, email=EMAIL_INVITE)
    assert len(invitations) == 1
    invitation = invitations[0]
    assert invitation.role == "proprietaire"
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
    EMAIL_INVITE = "bob"
    data = {
        "email": EMAIL_INVITE,
    }
    url = f"/droits/{entreprise.siren}"

    response = client.post(url, data=data, follow=True)

    invitations = Invitation.objects.filter(entreprise=entreprise, email=EMAIL_INVITE)
    assert len(invitations) == 0
    assert len(mailoutbox) == 0
    assert response.status_code == 200
    content = html.unescape(response.content.decode("utf-8"))
    assert "L'invitation a échoué car le formulaire contient des erreurs." in content
