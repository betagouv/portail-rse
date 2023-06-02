from django.core.management.base import BaseCommand

from entreprises.models import Entreprise as ImpactEntreprise
from entreprises.models import get_current_evolution
from metabase.models import Entreprise as MetabaseEntreprise


class Command(BaseCommand):
    def handle(self, *args, **options):
        self._drop_entreprises()
        self._insert_entreprises()

    def _drop_entreprises(self):
        MetabaseEntreprise.objects.all().delete()
        self._success("Suppression des entreprises de Metabase: OK")

    def _insert_entreprises(self):
        for entreprise in ImpactEntreprise.objects.all():
            evolution = get_current_evolution(entreprise)
            meta_e = MetabaseEntreprise.objects.create(
                siren=entreprise.siren,
                denomination=entreprise.denomination,
                bdese_accord=evolution.bdese_accord,
                effectif=evolution.effectif,
                created_at=entreprise.created_at,
                updated_at=entreprise.updated_at,
            )
            meta_e.save()
            self._success(str(entreprise))

    def _success(self, message):
        self.stdout.write(self.style.SUCCESS(message))
