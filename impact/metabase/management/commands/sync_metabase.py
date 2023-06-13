from django.core.management.base import BaseCommand

from entreprises.models import Entreprise as ImpactEntreprise
from entreprises.models import Evolution
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
            evolution = entreprise.get_current_evolution()
            meta_e = MetabaseEntreprise.objects.create(
                siren=entreprise.siren,
                denomination=entreprise.denomination,
                bdese_accord=evolution.bdese_accord,
                effectif=evolution.effectif,
                created_at=entreprise.created_at,
                updated_at=_last_update(entreprise),
            )
            meta_e.save()
            self._success(str(entreprise))

    def _success(self, message):
        self.stdout.write(self.style.SUCCESS(message))


def _last_update(entreprise):
    last_update = entreprise.updated_at
    for evolution in Evolution.objects.filter(entreprise=entreprise):
        if evolution.updated_at > last_update:
            last_update = evolution.updated_at
    return last_update
