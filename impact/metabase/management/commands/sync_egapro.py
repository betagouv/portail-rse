import asyncio
import json
from datetime import datetime

import aiohttp
from django.conf import settings
from django.core.management.base import BaseCommand

from entreprises.models import Entreprise
from metabase.models import TempEgaPro

FETCH_URL = "https://egapro.travail.gouv.fr/api/public/declaration/%s/%s"

# utilise un settings via variable d'evironnement nommé METABASE_NB_ASYNC_CALLS
NB_APPELS = settings.METABASE_NB_ASYNC_CALLS


class Command(BaseCommand):
    help = "Récupération des données API EgaPro"

    def add_arguments(self, parser):
        parser.add_argument(
            "--keep",
            action="store_true",
            help="Conserver les données EgaPro existantes dans la table de travail",
        )
        parser.add_argument(
            "--export",
            action="store_true",
            help="Activer l'export des données EgaPro sous forme de fichier JSON",
        )
        parser.add_argument(
            "--export_file",
            type=str,
            default="egapro.json",
            help="Nom du fichier JSON pour l'export des données EgaPro",
        )

    def handle(self, *args, **options):
        keep = options["keep"]
        export = options["export"]
        export_file = options["export_file"]

        self.stdout.write(self.style.SUCCESS("Import des données EgaPro"))

        start_time = datetime.now()
        self._process(keep, export, export_file)
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()

        self.stdout.write(
            self.style.SUCCESS(
                f"Commande exécutée avec succès en {processing_time:.2f} secondes"
            )
        )

    def _process(self, keep, export, export_file):
        annee_courante = datetime.now().year - 1

        if not keep:
            self.stdout.write(
                self.style.NOTICE(" > effacement des données précédentes")
            )
            TempEgaPro.objects.filter(annee=annee_courante).delete()

        declaration_existantes = (
            TempEgaPro.objects.filter(annee=annee_courante)
            .exclude(reponse_api=None)
            .values_list("siren", flat=True)
        )

        # attention : pas sur la meme DB (metabase)
        declaration_existantes = list(declaration_existantes)

        # récupére le champ SIREN de tous les objets "Entreprise"
        entreprises = Entreprise.objects.exclude(
            siren__in=declaration_existantes
        ).values_list("siren", flat=True)

        # pour éviter de faire des appels "lazy" pendant une opération asynchrone de Django
        entreprises = list(entreprises)
        result = dict()

        # récupére les entreprises en asynchrone via aiohttp
        async def fetch_data(session, entreprise):
            url = FETCH_URL % (entreprise, datetime.now().year - 1)
            async with session.get(url) as response:
                match response.status:
                    case 200:
                        return entreprise, await response.json()
                    case 404:
                        return None
                    case _:
                        print(f"ERREUR {response.status}:", entreprise)
                        return None

        # limite à NB_APPELS le nombre de requêtes simultanées (via sémaphore)
        async def fetch_all_data():
            async with aiohttp.ClientSession() as session:
                tasks = []
                async with asyncio.Semaphore(NB_APPELS):
                    for entreprise in entreprises:
                        tasks.append(fetch_data(session, entreprise))
                    responses = await asyncio.gather(*tasks)
                    for pairs in responses:
                        if pairs:
                            siren, response = pairs
                            result[siren] = response

        asyncio.run(fetch_all_data())

        # enregistrement dans la table de travail
        self._maj_table_temp_egapro(result)

        if export:
            with open(export_file, "w") as f:
                # JSON est censé toujours être de l'UTF (8 ou 16) :
                # pas besoin de l'ecodage ASCII
                json.dump(result, f, ensure_ascii=False, indent=4)
            self.stdout.write(
                self.style.SUCCESS(
                    f"> export des données EgaPro vers le fichier '{export_file}' effectué avec succès"
                )
            )

    def _maj_table_temp_egapro(self, results):
        rs = []
        annee_courante = datetime.now().year - 1
        for siren, resp in results.items():
            if resp:
                record = TempEgaPro(annee=annee_courante, siren=siren, reponse_api=resp)
                rs.append(record)

        TempEgaPro.objects.bulk_create(rs)
