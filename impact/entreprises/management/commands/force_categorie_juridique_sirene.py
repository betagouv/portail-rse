from django.core.management.base import BaseCommand

import api.exceptions
import api.recherche_entreprises
from entreprises.models import Entreprise


class Command(BaseCommand):
    def handle(self, *args, **options):
        for entreprise in Entreprise.objects.all():
            if entreprise.denomination:
                print(f"IGNORE: {entreprise.siren} {entreprise.denomination}")
            else:
                try:
                    infos_entreprise = api.recherche_entreprises.recherche(
                        entreprise.siren
                    )
                    entreprise.categorie_juridique_sirene = infos_entreprise[
                        "categorie_juridique_sirene"
                    ]
                    entreprise.save()
                    print(f"OK: {entreprise.siren} {entreprise.denomination}")
                except api.exceptions.APIError as e:
                    print(f"ERREUR {e}: {entreprise.siren}")
