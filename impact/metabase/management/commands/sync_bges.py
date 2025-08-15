import asyncio
import csv
from datetime import datetime

import aiohttp
from django.core.management.base import BaseCommand
from six import StringIO

from api.exceptions import APIError
from metabase.models import TempBGES

BASE_API_URL = "https://bilans-ges.ademe.fr"
MEDIAS_URL = f"{BASE_API_URL}/api/exports/public-inventories/latest"


class Command(BaseCommand):
    help = "Récupération des données Bilan GES"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Import des données BGES"))

        start_time = datetime.now()
        self._process()
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()

        self.stdout.write(
            self.style.SUCCESS(
                f"Commande exécutée avec succès en {processing_time:.2f} secondes"
            )
        )

    def _process(self):
        self.stdout.write(self.style.NOTICE(" > effacement des données précédentes"))

        TempBGES.objects.all().delete()
        result = asyncio.run(self._fetch_last_bges_file())

        # enregistrement dans la table de travail
        self._maj_table_temp_bges(result)

    async def _fetch_file_url(self, session) -> str:
        # récupère la dernière version du fichier d'export BGES
        async with session.get(MEDIAS_URL) as response:
            content = await response.json()

            if file_path := content.get("file"):
                return f"{BASE_API_URL}/{file_path}/download"

            raise APIError("Impossible de déterminer l'URL du fichier BGES")

    async def _fetch_last_bges_file(self):
        async with aiohttp.ClientSession() as session:
            # récupère la dernière version du fichier d'export BGES (metadonnées)
            last_file_url = await self._fetch_file_url(session)
            self.stdout.write(
                self.style.NOTICE(f" > téléchargement de : {last_file_url}")
            )

            # récupère le fichier proprement dit et en extrait les données
            async with session.get(last_file_url) as response:
                # la réponse est au format CSV, il serait préférable de la streamer (30+Mb)
                # mais io.StreamReader n'est pas vraiment un reader directement comptatible
                # pour streamer un CSV
                return self._extract_bges_data(await response.text())

    def _extract_bges_data(self, content):
        result = []
        with StringIO(content) as f:
            for line in csv.DictReader(f, delimiter=";"):
                # on ne garde que quelques éléments
                result.append(
                    {
                        "siren": line["SIREN principal"],
                        "dt_publication": datetime.strptime(
                            line["Date de publication"], "%d/%m/%Y"
                        ),
                    }
                )
        return result

    def _maj_table_temp_bges(self, results):
        rs = []
        for r in results:
            record = TempBGES(**r)
            rs.append(record)

        TempBGES.objects.bulk_create(rs)
