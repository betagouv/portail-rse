import pytest

from users.forms import CreationCompteEtrangerForm
from users.forms import message_erreur_administrateurs
from users.forms import ProconnectUserEditionForm
from users.forms import UserEditionForm
from users.forms import UserPasswordForm


def test_echec_si_mot_de_passe_trop_faible(db, alice):
    data = {
        "password1": "password",
        "password2": "password",
    }

    bound_form = UserPasswordForm(data, instance=alice)

    assert not bound_form.is_valid()
    assert bound_form.errors["password1"] == [
        "Ce mot de passe est trop court. Il doit contenir au minimum 12 caractères.",
        "Ce mot de passe est trop courant.",
        "Le mot de passe doit contenir au moins une minuscule, une majuscule, un chiffre et un caractère spécial",
    ]


def test_message_si_l_entreprise_a_un_ou_des_administrateurs(db, alice, bob):
    alice.email = "alice.cooper@mail.example"
    alice.save()
    bob.email = "bob@domaine.test"
    bob.save()

    assert (
        message_erreur_administrateurs([alice])
        == "Il existe déjà un administrateur sur cette entreprise. Contactez la personne concernée (a**********r@mail.example) ou notre support (contact@portail-rse.beta.gouv.fr)."
    )

    assert (
        message_erreur_administrateurs([alice, bob])
        == "Il existe déjà des administrateurs sur cette entreprise. Contactez une des personnes concernées (a**********r@mail.example, b*b@domaine.test) ou notre support (contact@portail-rse.beta.gouv.fr)."
    )


@pytest.mark.parametrize("form_class", [UserEditionForm, ProconnectUserEditionForm])
@pytest.mark.parametrize("champ", ["prenom", "nom"])
def test_echec_si_balise_html_dans_prenom_ou_nom(db, alice, form_class, champ):
    data = {
        "prenom": "Alice",
        "nom": "User",
        "email": alice.email,
    }
    data[champ] = "<script>alert(1)</script>"

    bound_form = form_class(data, instance=alice)

    assert not bound_form.is_valid()
    assert bound_form.errors[champ] == ["Les caractères < et > ne sont pas autorisés."]


def test_echec_si_balise_html_dans_email(db, alice):
    data = {
        "prenom": "Alice",
        "nom": "User",
        "email": '"<script>alert(1)</script>"@domaine.test',
    }

    bound_form = UserEditionForm(data, instance=alice)

    assert not bound_form.is_valid()
    assert bound_form.errors["email"] == [
        "Les caractères < et > ne sont pas autorisés."
    ]


def test_creation_compte_etranger_marque_l_utilisateur_comme_non_francais(db):
    data = {
        "email": "user@domaine.test",
        "password1": "Passw0rd!123",
        "password2": "Passw0rd!123",
        "prenom": "Alice",
        "nom": "User",
        "acceptation_cgu": "checked",
    }

    bound_form = CreationCompteEtrangerForm(data)

    assert bound_form.is_valid(), bound_form.errors
    user = bound_form.save()
    assert not user.est_francais
    assert user.is_conseiller_rse is False
    assert not user.reception_actualites


@pytest.mark.parametrize("champ", ["prenom", "nom"])
def test_creation_compte_etranger_echec_si_balise_html_dans_prenom_ou_nom(db, champ):
    data = {
        "email": "user@domaine.test",
        "password1": "Passw0rd!123",
        "password2": "Passw0rd!123",
        "prenom": "Alice",
        "nom": "User",
        "acceptation_cgu": "checked",
    }
    data[champ] = "<script>alert(1)</script>"

    bound_form = CreationCompteEtrangerForm(data)

    assert not bound_form.is_valid()
    assert bound_form.errors[champ] == ["Les caractères < et > ne sont pas autorisés."]
