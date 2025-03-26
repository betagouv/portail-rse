import pytest

from habilitations.models import attach_user_to_entreprise
from users.management.commands.import_utilisateurs_brevo import Command


@pytest.mark.django_db(transaction=True)
def test_import_des_contacts(
    db, mocker, settings, alice, entreprise_non_qualifiee, entreprise_factory
):
    alice.is_email_confirmed = True
    attach_user_to_entreprise(alice, entreprise_non_qualifiee, "Présidente")
    entreprise_non_qualifiee_2 = entreprise_factory(
        siren="111111111", denomination="Artisans", tranche_bilan=None
    )
    attach_user_to_entreprise(alice, entreprise_non_qualifiee_2, "Présidente")
    entreprise_qualifiee = entreprise_factory(
        siren="222222222", denomination="Coopérative"
    )
    attach_user_to_entreprise(alice, entreprise_qualifiee, "Présidente")
    settings.BREVO_API_KEY = "BREVO_API_KEY"
    mocked_import_contacts = mocker.patch(
        "sib_api_v3_sdk.ContactsApi.import_contacts",
    )

    Command().handle(list_id=42)

    assert mocked_import_contacts.called
    args, _ = mocked_import_contacts.call_args
    request_contact_import = args[0]
    assert request_contact_import.json_body == [
        {
            "email": alice.email,
            "attributes": {
                "PORTAIL_RSE_ID": alice.id,
                "PORTAIL_RSE_DATE_INSCRIPTION": alice.created_at.strftime("%d-%m-%Y"),
                "EMAIL_CONFIRME": "yes",
                "ENTREPRISES_NON_QUALIFIEES": f"{entreprise_non_qualifiee.denomination}, {entreprise_non_qualifiee_2.denomination}",
            },
        }
    ]
    assert request_contact_import.list_ids == [42]
    assert request_contact_import.update_existing_contacts == True
    assert request_contact_import.empty_contacts_attributes == True
