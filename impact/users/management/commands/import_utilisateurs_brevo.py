from django.conf import settings
from django.core.management.base import BaseCommand
from sib_api_v3_sdk import ApiClient
from sib_api_v3_sdk import Configuration
from sib_api_v3_sdk import ContactsApi
from sib_api_v3_sdk import RequestContactImport

from users.models import User


def _client_api():
    configuration = Configuration()
    configuration.api_key["api-key"] = settings.BREVO_API_KEY
    return ApiClient(configuration)


class Command(BaseCommand):
    help = "Importe les utilisateurs dans Brevo"

    def add_arguments(self, parser):
        parser.add_argument(
            "list_id",
            nargs="?",
            type=int,
            help="ID de la liste de contacts Brevo dans laquelle les utilisateurs seront importés. Si aucun ID n'est fourni, la commande ne fait rien.",
        )

    def handle(self, *args, **options):
        list_id = options["list_id"]
        if list_id is None:
            self.stdout.write(
                self.style.SUCCESS(
                    "Aucun ID de liste de contacts fourni. Import des utilisateurs dans Brevo annulé."
                )
            )
            return
        client_api = _client_api()
        api_instance = ContactsApi(client_api)
        request_contact_import = RequestContactImport()
        request_contact_import.json_body = [
            {
                "email": user.email,
                "attributes": {
                    "EXT_ID": user.id,
                    "PORTAIL_RSE_ID": user.id,
                    "PORTAIL_RSE_DATE_INSCRIPTION": f"{user.created_at:%d-%m-%Y}",
                    "EMAIL_CONFIRME": "yes" if user.is_email_confirmed else None,
                    "CONSEILLER_RSE": "yes" if user.is_conseiller_rse else None,
                    "ENTREPRISES_NON_QUALIFIEES": ", ".join(
                        [
                            entreprise.denomination
                            for entreprise in user.entreprises
                            if not entreprise.dernieres_caracteristiques_qualifiantes
                        ]
                    ),
                },
            }
            for user in User.objects.all()
        ]
        request_contact_import.list_ids = [list_id]
        request_contact_import.update_existing_contacts = True
        request_contact_import.empty_contacts_attributes = True
        api_instance.import_contacts(request_contact_import)
        self.stdout.write(
            self.style.SUCCESS("Import des utilisateurs dans Brevo teminé.")
        )
