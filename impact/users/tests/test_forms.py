from habilitations.models import Habilitation
from users.forms import InvitationForm
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


def test_échec_lors_de_la_création_car_un_propriétaire_de_l_entreprise_existe_déjà(
    db, alice, entreprise_non_qualifiee
):
    Habilitation.ajouter(entreprise_non_qualifiee, alice, fonctions="Présidente")
    data = {
        "prenom": "Bob",
        "nom": "User",
        "email": "user@domaine.test",
        "password1": "password",
        "password2": "password",
        "siren": entreprise_non_qualifiee.siren,
        "acceptation_cgu": "checked",
        "fonctions": "Présidente",
    }

    bound_form = UserCreationForm(data)

    assert not bound_form.is_valid()
    assert bound_form.errors["siren"] == [
        "Cette entreprise a déjà au moins un propriétaire.",
    ]
    assert bound_form.proprietaires_presents == [alice]
    assert (
        bound_form.message_erreur_proprietaires()
        == "Il existe déjà un propriétaire sur cette entreprise. Contactez la personne dans l'entreprise qui possède ce compte ("
        + alice.email
        + ")."
    )


def test_succès_lors_de_l_invitation(db, entreprise_non_qualifiee):
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

    bound_form = InvitationForm(data)

    assert bound_form.is_valid()


def test_erreur_lors_de_l_invitation_car_l_entreprise_n_existe_pas(
    db, entreprise_non_qualifiee
):
    data = {
        "prenom": "Alice",
        "nom": "User",
        "email": "user@domaine.test",
        "password1": "Passw0rd!123",
        "password2": "Passw0rd!123",
        "siren": "123456789",
        "acceptation_cgu": "checked",
        "fonctions": "Présidente",
    }

    bound_form = InvitationForm(data)

    assert not bound_form.is_valid()
    assert bound_form.errors["siren"] == [
        "Cette entreprise n'existe plus dans Portail-RSE.",
    ]
