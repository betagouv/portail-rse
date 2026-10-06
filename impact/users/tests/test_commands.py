from datetime import date

import pytest
from dateutil.relativedelta import relativedelta
from django.core.management import call_command
from freezegun import freeze_time

from habilitations.models import Habilitation
from habilitations.models import UserRole


@pytest.mark.django_db(transaction=True)
def test_import_des_contacts(
    db, mocker, settings, alice, entreprise_non_qualifiee, entreprise_factory
):
    alice.is_email_confirmed = True
    alice.is_conseiller_rse = True
    alice.save()
    Habilitation.ajouter(entreprise_non_qualifiee, alice, fonctions="Présidente")
    entreprise_non_qualifiee_2 = entreprise_factory(
        siren="111111111", denomination="Artisans", tranche_bilan=None
    )
    Habilitation.ajouter(entreprise_non_qualifiee_2, alice, fonctions="Présidente")
    entreprise_qualifiee = entreprise_factory(
        siren="222222222", denomination="Coopérative"
    )
    Habilitation.ajouter(
        entreprise_qualifiee, alice, fonctions="Présidente", role=UserRole.CONTRIBUTEUR
    )
    settings.BREVO_API_KEY = "BREVO_API_KEY"
    mocked_import_contacts = mocker.patch(
        "sib_api_v3_sdk.ContactsApi.import_contacts",
    )

    call_command("import_utilisateurs_brevo", 42)

    assert mocked_import_contacts.called
    args, _ = mocked_import_contacts.call_args
    request_contact_import = args[0]
    assert request_contact_import.json_body == [
        {
            "email": alice.email,
            "attributes": {
                "EXT_ID": alice.id,
                "PORTAIL_RSE_ID": alice.id,
                "PORTAIL_RSE_DATE_INSCRIPTION": alice.created_at.strftime("%d-%m-%Y"),
                "EMAIL_CONFIRME": "yes",
                "CONSEILLER_RSE": "yes",
                "ENTREPRISES_NON_QUALIFIEES": f"{entreprise_non_qualifiee.denomination}, {entreprise_non_qualifiee_2.denomination}",
            },
        }
    ]
    assert request_contact_import.list_ids == [42]
    assert request_contact_import.update_existing_contacts == True
    assert request_contact_import.empty_contacts_attributes == True


def test_import_des_contacts_annulé_si_list_id_absent(mocker, settings):
    settings.BREVO_API_KEY = "BREVO_API_KEY"
    mocked_import_contacts = mocker.patch(
        "sib_api_v3_sdk.ContactsApi.import_contacts",
    )

    call_command("import_utilisateurs_brevo")

    assert not mocked_import_contacts.called


@pytest.mark.django_db(transaction=True)
def test_supprime_utilisateurs_non_confirmes(django_user_model):
    il_y_a_deux_mois = date.today() + relativedelta(months=-2)
    il_y_a_moins_de_deux_mois = il_y_a_deux_mois + relativedelta(days=1)
    il_y_a_plus_de_deux_mois = il_y_a_deux_mois + relativedelta(days=-1)

    with freeze_time(il_y_a_plus_de_deux_mois) as frozen_datetime:
        alice = django_user_model.objects.create(
            email="alice@portail-rse.test",
            is_email_confirmed=False,
        )
        bob = django_user_model.objects.create(
            email="bob@portail-rse.test",
            is_email_confirmed=True,
        )

    with freeze_time(il_y_a_moins_de_deux_mois) as frozen_datetime:
        charlie = django_user_model.objects.create(
            email="charlie@portail-rse.test",
            is_email_confirmed=False,
        )

    call_command("supprime_utilisateurs_non_confirmes_ou_non_revenus")

    with pytest.raises(django_user_model.DoesNotExist):
        assert alice.refresh_from_db()
    bob.refresh_from_db()
    charlie.refresh_from_db()


@pytest.mark.django_db(transaction=True)
def test_check_supprime_utilisateurs_non_confirmes(django_user_model):
    il_y_a_deux_mois = date.today() + relativedelta(months=-2)
    il_y_a_plus_de_deux_mois = il_y_a_deux_mois + relativedelta(days=-1)

    with freeze_time(il_y_a_plus_de_deux_mois) as frozen_datetime:
        alice = django_user_model.objects.create(
            email="alice@portail-rse.test",
            is_email_confirmed=False,
        )

    call_command("supprime_utilisateurs_non_confirmes_ou_non_revenus", check=True)

    alice.refresh_from_db()


@pytest.mark.django_db(transaction=True)
def test_anonymise_utilisateurs_non_revenus(django_user_model):
    il_y_a_quatre_ans = date.today() + relativedelta(years=-4)
    il_y_a_trois_ans = date.today() + relativedelta(years=-3)
    il_y_a_moins_de_trois_ans = il_y_a_trois_ans + relativedelta(days=1)
    il_y_a_plus_de_trois_ans = il_y_a_trois_ans + relativedelta(days=-1)

    with freeze_time(il_y_a_quatre_ans) as frozen_datetime:
        alice = django_user_model.objects.create(
            prenom="Alice",
            nom="Cooper",
            email="alice@portail-rse.test",
            is_email_confirmed=True,
        )
        bob = django_user_model.objects.create(
            prenom="Bob",
            nom="NOM",
            email="bob@portail-rse.test",
            is_email_confirmed=True,
        )

    alice.last_login = il_y_a_plus_de_trois_ans
    alice.save()

    bob.last_login = il_y_a_moins_de_trois_ans
    bob.save()

    call_command("supprime_utilisateurs_non_confirmes_ou_non_revenus")

    alice.refresh_from_db()
    assert alice.prenom == "Personne"
    assert alice.nom == "anonymisée"
    assert alice.email == str(alice.id) + "@anonyme.invalid"
    assert not alice.is_active
    bob.refresh_from_db()
    assert bob.prenom == "Bob"
    assert bob.nom == "NOM"
    assert bob.email == "bob@portail-rse.test"
    assert bob.is_active
