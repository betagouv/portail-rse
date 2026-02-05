import pytest
from django.urls import reverse

from entreprises.models import Entreprise
from habilitations.enums import UserRole
from habilitations.models import Habilitation
from invitations.models import Invitation


@pytest.fixture
def conseiller_rse(django_user_model):
    return django_user_model.objects.create(
        prenom="Claire",
        nom="Conseillère",
        email="claire@conseil-rse.test",
        is_email_confirmed=True,
        is_conseiller_rse=True,
    )


@pytest.mark.django_db
def test_tableau_de_bord_conseiller_acces_refuse_non_conseiller(client, alice):
    """Un utilisateur non-conseiller ne peut pas accéder au tableau de bord conseiller."""
    client.force_login(alice)

    response = client.get(reverse("users:tableau_de_bord_conseiller"))

    assert response.status_code == 302


@pytest.mark.django_db
def test_tableau_de_bord_conseiller_affiche_page(client, conseiller_rse):
    """Un conseiller RSE peut accéder au tableau de bord conseiller."""
    client.force_login(conseiller_rse)

    response = client.get(reverse("users:tableau_de_bord_conseiller"))

    assert response.status_code == 200
    assert "Espace Conseiller RSE" in response.content.decode()


@pytest.mark.django_db
def test_tableau_de_bord_conseiller_affiche_entreprises_en_gestion(
    client, conseiller_rse, entreprise_factory
):
    """Le tableau de bord affiche les entreprises en gestion du conseiller."""
    entreprise1 = entreprise_factory(siren="123456789")
    entreprise2 = entreprise_factory(siren="987654321")

    Habilitation.ajouter(entreprise1, conseiller_rse, UserRole.EDITEUR)
    Habilitation.ajouter(entreprise2, conseiller_rse, UserRole.EDITEUR)

    client.force_login(conseiller_rse)
    response = client.get(reverse("users:tableau_de_bord_conseiller"))

    assert response.status_code == 200
    content = response.content.decode()
    assert entreprise1.denomination in content
    assert entreprise2.denomination in content


@pytest.mark.django_db
def test_rattachement_entreprise_existante_avec_proprietaire(
    client, conseiller_rse, alice, entreprise_factory
):
    """Un conseiller ne peut pas se rattacher à une entreprise avec un propriétaire."""
    entreprise = entreprise_factory(siren="123456789")
    Habilitation.ajouter(entreprise, alice, UserRole.PROPRIETAIRE)

    client.force_login(conseiller_rse)
    response = client.post(
        reverse("users:tableau_de_bord_conseiller"),
        {"siren": "123456789", "fonctions": "Consultant CSRD"},
    )

    assert (
        Habilitation.objects.filter(entreprise=entreprise, user=conseiller_rse).count()
        == 0
    )


@pytest.mark.django_db
def test_rattachement_entreprise_inexistante(client, conseiller_rse):
    """Un conseiller peut se rattacher à une entreprise inexistante."""
    client.force_login(conseiller_rse)

    response = client.post(
        reverse("users:tableau_de_bord_conseiller"),
        {
            "siren": "999999999",
            "fonctions": "Consultant CSRD",
            "email_futur_proprietaire": "futur@proprietaire.test",
        },
        follow=True,
    )

    entreprise = Entreprise.objects.get(siren="999999999")
    assert Habilitation.existe(entreprise, conseiller_rse)
    habilitation = Habilitation.pour(entreprise, conseiller_rse)
    assert habilitation.role == UserRole.PROPRIETAIRE
    assert habilitation.is_conseiller_rse
    assert habilitation.fonctions == "Consultant CSRD"
    invitation = Invitation.objects.get(
        entreprise=entreprise, email="futur@proprietaire.test"
    )
    assert invitation.role == UserRole.PROPRIETAIRE


@pytest.mark.django_db
def test_rattachement_entreprise_sans_proprietaire(
    client, conseiller_rse, entreprise_factory
):
    """Un conseiller peut se rattacher à une entreprise sans propriétaire."""
    entreprise = entreprise_factory(siren="123456789")
    # Aucun propriétaire ajouté

    client.force_login(conseiller_rse)
    response = client.post(
        reverse("users:tableau_de_bord_conseiller"),
        {
            "siren": "123456789",
            "fonctions": "Consultant CSRD",
            "email_futur_proprietaire": "futur@proprietaire.test",
        },
        follow=True,
    )

    assert Habilitation.existe(entreprise, conseiller_rse)
    habilitation = Habilitation.pour(entreprise, conseiller_rse)
    assert habilitation.role == UserRole.PROPRIETAIRE
    assert habilitation.is_conseiller_rse
    assert habilitation.fonctions == "Consultant CSRD"
    invitation = Invitation.objects.get(
        entreprise=entreprise, email="futur@proprietaire.test"
    )
    assert invitation.role == UserRole.PROPRIETAIRE


@pytest.mark.django_db
def test_rattachement_deja_existant(client, conseiller_rse, alice, entreprise_factory):
    """Un conseiller ne peut pas se rattacher deux fois à la même entreprise."""
    entreprise = entreprise_factory(siren="123456789")
    Habilitation.ajouter(entreprise, alice, UserRole.PROPRIETAIRE)
    Habilitation.ajouter(entreprise, conseiller_rse, UserRole.EDITEUR)

    client.force_login(conseiller_rse)
    response = client.post(
        reverse("users:tableau_de_bord_conseiller"),
        {
            "siren": "123456789",
            "fonctions": "Consultant CSRD",
            "email_futur_proprietaire": "futur@proprietaire.test",
        },
        follow=True,
    )

    assert "déjà rattaché" in response.content.decode()


@pytest.mark.django_db
def test_lien_espace_conseiller_visible_pour_conseiller(
    client, conseiller_rse, entreprise_factory, alice
):
    """Le lien 'Espace conseillers RSE' est visible dans l'entête pour un conseiller RSE."""
    entreprise = entreprise_factory(siren="123456789")
    Habilitation.ajouter(entreprise, alice, UserRole.PROPRIETAIRE)
    # Le conseiller doit aussi être rattaché à l'entreprise pour accéder au tableau de bord
    Habilitation.ajouter(entreprise, conseiller_rse, UserRole.EDITEUR)

    client.force_login(conseiller_rse)
    response = client.get(
        reverse("reglementations:tableau_de_bord", kwargs={"siren": "123456789"})
    )

    content = response.content.decode()
    assert "Espace conseillers RSE" in content
    assert reverse("users:tableau_de_bord_conseiller") in content


@pytest.mark.django_db
def test_lien_espace_conseiller_invisible_pour_non_conseiller(
    client, alice, entreprise_factory
):
    """Le lien 'Espace conseillers RSE' n'est pas visible pour un utilisateur non-conseiller."""
    entreprise = entreprise_factory(siren="123456789")
    Habilitation.ajouter(entreprise, alice, UserRole.PROPRIETAIRE)

    client.force_login(alice)
    response = client.get(
        reverse("reglementations:tableau_de_bord", kwargs={"siren": "123456789"})
    )

    content = response.content.decode()
    assert "Espace conseillers RSE" not in content
