import pytest
from django.urls import reverse

from entreprises.models import Entreprise
from habilitations.enums import UserRole
from habilitations.models import Habilitation
from invitations.models import Invitation


def test_tableau_de_bord_conseiller_affiche_entreprises_en_gestion(
    client, conseiller_rse, entreprise_factory
):
    """Le tableau de bord affiche les entreprises en gestion du conseiller."""
    entreprise1 = entreprise_factory(identifiant="123456789")
    entreprise2 = entreprise_factory(identifiant="987654321")

    Habilitation.ajouter(entreprise1, conseiller_rse, UserRole.CONTRIBUTEUR)
    Habilitation.ajouter(entreprise2, conseiller_rse, UserRole.CONTRIBUTEUR)

    client.force_login(conseiller_rse)
    response = client.get(reverse("tableau_de_bord:conseiller"))

    assert response.status_code == 200
    content = response.content.decode()
    assert entreprise1.denomination in content
    assert entreprise2.denomination in content


def test_tableau_de_bord_conseiller_affiche_le_libelle_d_identifiant_selon_le_pays(
    client, conseiller_rse, entreprise_factory
):
    entreprise_francaise = entreprise_factory(identifiant="123456789")
    entreprise_etrangere = entreprise_factory(
        code_pays="MAR", identifiant="001234567000089"
    )
    Habilitation.ajouter(entreprise_francaise, conseiller_rse, UserRole.CONTRIBUTEUR)
    Habilitation.ajouter(entreprise_etrangere, conseiller_rse, UserRole.CONTRIBUTEUR)
    client.force_login(conseiller_rse)

    response = client.get(reverse("tableau_de_bord:conseiller"))

    content = response.content.decode()
    assert "SIREN : 123456789" in content
    assert "ICE : 001234567000089" in content


def test_rattachement_entreprise_existante_avec_administrateur(
    client, conseiller_rse, alice, entreprise_factory
):
    """Un conseiller ne peut pas se rattacher à une entreprise avec un administrateur."""
    entreprise = entreprise_factory(identifiant="123456789")
    Habilitation.ajouter(entreprise, alice, UserRole.ADMINISTRATEUR)

    client.force_login(conseiller_rse)
    response = client.post(
        reverse("tableau_de_bord:conseiller"),
        {"siren": "123456789", "fonctions": "Consultant CSRD"},
    )

    assert (
        Habilitation.objects.filter(entreprise=entreprise, user=conseiller_rse).count()
        == 0
    )


@pytest.mark.network
def test_rattachement_entreprise_inexistante(
    client, conseiller_rse, mock_api_infos_entreprise
):
    """Un conseiller peut se rattacher à une entreprise inexistante."""
    client.force_login(conseiller_rse)
    SIREN = mock_api_infos_entreprise.return_value["siren"]

    response = client.post(
        reverse("tableau_de_bord:conseiller"),
        {
            "siren": SIREN,
            "email_futur_administrateur": "futur@entreprise.test",
        },
        follow=True,
    )

    entreprise = Entreprise.objects.get(code_pays="FRA", identifiant=SIREN)
    assert Habilitation.existe(entreprise, conseiller_rse)
    habilitation = Habilitation.pour(entreprise, conseiller_rse)
    assert habilitation.role == UserRole.ADMINISTRATEUR
    assert habilitation.is_conseiller_rse
    assert not habilitation.fonctions
    invitation = Invitation.objects.get(
        entreprise=entreprise, email="futur@entreprise.test"
    )
    assert invitation.role == UserRole.ADMINISTRATEUR


def test_rattachement_deja_existant(client, conseiller_rse, alice, entreprise_factory):
    """Un conseiller ne peut pas se rattacher deux fois à la même entreprise."""
    entreprise = entreprise_factory(identifiant="123456782")
    Habilitation.ajouter(entreprise, alice, UserRole.ADMINISTRATEUR)
    Habilitation.ajouter(entreprise, conseiller_rse, UserRole.CONTRIBUTEUR)

    client.force_login(conseiller_rse)
    response = client.post(
        reverse("tableau_de_bord:conseiller"),
        {
            "siren": "123456782",
            "email_futur_administrateur": "futur@proprietaire.test",
        },
        follow=True,
    )

    assert "déjà rattaché" in response.content.decode()


def test_lien_espace_conseiller_visible_pour_conseiller(
    client, conseiller_rse, entreprise_factory, alice
):
    """Le lien 'Espace conseillers RSE' est visible dans l'entête pour un conseiller RSE."""
    entreprise = entreprise_factory(identifiant="123456789")
    Habilitation.ajouter(entreprise, alice, UserRole.ADMINISTRATEUR)
    # Le conseiller doit aussi être rattaché à l'entreprise pour accéder au tableau de bord
    Habilitation.ajouter(entreprise, conseiller_rse, UserRole.CONTRIBUTEUR)

    client.force_login(conseiller_rse)
    response = client.get(
        reverse(
            "tableau_de_bord:resume",
            kwargs={"id_public": entreprise.id_public},
        )
    )

    content = response.content.decode()
    assert "Espace conseillers RSE" in content
    assert reverse("tableau_de_bord:conseiller") in content


def test_lien_espace_conseiller_invisible_pour_non_conseiller(
    client, alice, entreprise_factory
):
    """Le lien 'Espace conseillers RSE' n'est pas visible pour un utilisateur non-conseiller."""
    entreprise = entreprise_factory(identifiant="123456789")
    Habilitation.ajouter(entreprise, alice, UserRole.ADMINISTRATEUR)

    client.force_login(alice)
    response = client.get(
        reverse(
            "tableau_de_bord:resume",
            kwargs={"id_public": entreprise.id_public},
        )
    )

    content = response.content.decode()
    assert "Espace conseillers RSE" not in content
