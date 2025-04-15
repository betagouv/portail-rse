import time

from django.core.management.base import BaseCommand

import api.exceptions
import api.recherche_entreprises
from entreprises.models import Entreprise


class Command(BaseCommand):
    def handle(self, *args, **options):
        for entreprise in Entreprise.objects.all():
            if entreprise.code_NAF:
                print(
                    f"IGNORE: {entreprise.siren} {entreprise.denomination} {entreprise.code_NAF}"
                )
            else:
                try:
                    maj(entreprise)
                    print(
                        f"OK: {entreprise.siren} {entreprise.denomination} {entreprise.code_NAF}"
                    )
                except api.exceptions.TooManyRequestError as e:
                    time.sleep(1)
                    maj(entreprise)
                    print(
                        f"OK (2): {entreprise.siren} {entreprise.denomination} {entreprise.code_NAF}"
                    )
                except api.exceptions.APIError as e:
                    print(f"ERREUR {e}: {entreprise.siren}")


def maj(entreprise):
    infos_entreprise = api.recherche_entreprises.recherche_par_siren(entreprise.siren)
    entreprise.code_NAF = infos_entreprise["code_NAF"]
    entreprise.save()
