from django.core.management.base import BaseCommand

import api.exceptions
import api.recherche_entreprises
from entreprises.models import Entreprise


class Command(BaseCommand):
    def handle(self, *args, **options):
        for entreprise in Entreprise.objects.all():
            if entreprise.raison_sociale:
                print(f"IGNORE: {entreprise.siren} {entreprise.raison_sociale}")
            else:
                try:
                    infos_entreprise = api.recherche_entreprises.recherche(
                        entreprise.siren
                    )
                    entreprise.raison_sociale = infos_entreprise["raison_sociale"]
                    entreprise.save()
                    print(f"OK: {entreprise.siren} {entreprise.raison_sociale}")
                except api.exceptions.APIError as e:
                    print(f"ERREUR {e}: {entreprise.siren}")
