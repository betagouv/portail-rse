from django.core.management.base import BaseCommand, CommandError
from entreprises.models import Entreprise as ImpactEntreprise
from metabase.models import Entreprise as MetabaseEntreprise


class Command(BaseCommand):
    def handle(self, *args, **options):
        for entreprise in ImpactEntreprise.objects.all():
            meta_e = MetabaseEntreprise.objects.create()
            meta_e.raison_sociale = entreprise.raison_sociale
            meta_e.siren = entreprise.siren
            meta_e.save()
            self.stdout.write(self.style.SUCCESS(entreprise))
