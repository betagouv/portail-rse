from users.forms import message_erreur_proprietaires
from users.forms import UserCreationForm


def test_fail_to_create_user_without_cgu(db):
    data = {
        "prenom": "Alice",
        "nom": "User",
        "email": "user@domaine.test",
        "password1": "Passw0rd!123",
        "password2": "Passw0rd!123",
        "siren": "123456789",
        "acceptation_cgu": "",
        "fonctions": "Présidente",
    }

    bound_form = UserCreationForm(data)

    assert not bound_form.is_valid()
    assert bound_form.errors["acceptation_cgu"] == ["Ce champ est obligatoire."]


def test_fail_to_create_user_with_invalid_siren(db):
    data = {
        "prenom": "Alice",
        "nom": "User",
        "email": "user@domaine.test",
        "password1": "Passw0rd!123",
        "password2": "Passw0rd!123",
        "siren": "123456abc",
        "acceptation_cgu": "checked",
        "fonctions": "Présidente",
    }

    bound_form = UserCreationForm(data)

    assert not bound_form.is_valid()
    assert bound_form.errors["siren"] == ["Le siren est incorrect"]


def test_fail_to_create_user_with_weak_password(db):
    data = {
        "prenom": "Alice",
        "nom": "User",
        "email": "user@domaine.test",
        "password1": "password",
        "password2": "password",
        "siren": "123456789",
        "acceptation_cgu": "checked",
        "fonctions": "Présidente",
    }

    bound_form = UserCreationForm(data)

    assert not bound_form.is_valid()
    assert bound_form.errors["password1"] == [
        "Ce mot de passe est trop court. Il doit contenir au minimum 12 caractères.",
        "Ce mot de passe est trop courant.",
        "Le mot de passe doit contenir au moins une minuscule, une majuscule, un chiffre et un caractère spécial",
    ]


def test_succès_lors_de_la_création_même_si_l_entreprise_existe_déjà(
    db, entreprise_non_qualifiee
):
    data = {
        "prenom": "Alice",
        "nom": "User",
        "email": "user@domaine.test",
        "password1": "Passw0rd!123",
        "password2": "Passw0rd!123",
        "siren": entreprise_non_qualifiee.siren,
        "acceptation_cgu": "checked",
        "fonctions": "Présidente",
    }

    bound_form = UserCreationForm(data)

    assert bound_form.is_valid()


def test_message_si_l_entreprise_a_un_ou_des_propriétaires(db, alice, bob):
    alice.email = "alice.cooper@mail.example"
    alice.save()
    bob.email = "bob@domaine.test"
    bob.save()

    assert (
        message_erreur_proprietaires([alice])
        == "Il existe déjà un propriétaire sur cette entreprise. Contactez la personne concernée (a**********r@mail.example) ou notre support (contact@portail-rse.beta.gouv.fr)."
    )

    assert (
        message_erreur_proprietaires([alice, bob])
        == "Il existe déjà des propriétaires sur cette entreprise. Contactez une des personnes concernées (a**********r@mail.example, b*b@domaine.test) ou notre support (contact@portail-rse.beta.gouv.fr)."
    )
