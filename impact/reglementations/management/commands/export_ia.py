import requests
from django.conf import settings
from django.core.management.base import BaseCommand

from reglementations.models import DocumentAnalyseIA


class Command(BaseCommand):
    def handle(self, *args, **options):
        url = f"{settings.IA_BASE_URL}/run-task"
        for document in DocumentAnalyseIA.objects.all():
            if (
                document.etat != "ok"
            ):  # filtrage en plus à faire + tri par date + limitation qté
                response = requests.post(
                    url, {"document_id": document.id, "url": document.url}
                )
                document.etat = response.json()["status"]
                document.save()
