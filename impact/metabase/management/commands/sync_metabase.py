from django.core.management.base import BaseCommand
from django.db.models import Count

from entreprises.models import CaracteristiquesAnnuelles
from entreprises.models import Entreprise as ImpactEntreprise
from habilitations.models import Habilitation as ImpactHabilitation
from metabase.models import Entreprise as MetabaseEntreprise
from metabase.models import Habilitation as MetabaseHabilitation
from metabase.models import Utilisateur as MetabaseUtilisateur
from users.models import User as ImpactUtilisateur


class Command(BaseCommand):
    def handle(self, *args, **options):
        self._drop_tables()
        self._insert_entreprises()
        self._insert_utilisateurs()
        self._insert_habilitations()

    def _drop_tables(self):
        MetabaseEntreprise.objects.all().delete()
        self._success("Suppression des entreprises de Metabase: OK")
        MetabaseUtilisateur.objects.all().delete()
        self._success("Suppression des utilisateurs de Metabase: OK")
        MetabaseHabilitation.objects.all().delete()
        self._success("Suppression des habilitations de Metabase: OK")

    def _insert_entreprises(self):
        self._success("Ajout des entreprises dans Metabase")
        for entreprise in ImpactEntreprise.objects.annotate(
            nombre_utilisateurs=Count("users")
        ):
            caracteristiques = entreprise.caracteristiques_actuelles()
            meta_e = MetabaseEntreprise.objects.create(
                impact_id=entreprise.pk,
                siren=entreprise.siren,
                denomination=entreprise.denomination,
                bdese_accord=caracteristiques.bdese_accord
                if caracteristiques
                else None,
                effectif=caracteristiques.effectif if caracteristiques else None,
                ajoutee_le=entreprise.created_at,
                modifiee_le=_last_update(entreprise),
                nombre_utilisateurs=entreprise.nombre_utilisateurs,
            )
            meta_e.save()
            self._success(str(entreprise))
        self._success("Ajout des entreprises dans Metabase: OK")

    def _insert_utilisateurs(self):
        self._success("Ajout des utilisateurs dans Metabase")
        for utilisateur in ImpactUtilisateur.objects.all():
            meta_u = MetabaseUtilisateur.objects.create(
                impact_id=utilisateur.pk,
                ajoute_le=utilisateur.created_at,
                modifie_le=utilisateur.updated_at,
                reception_actualites=utilisateur.reception_actualites,
                email_confirme=utilisateur.is_email_confirmed,
            )
            meta_u.save()
            self._success(str(utilisateur.pk))
        self._success("Ajout des utilisateurs dans Metabase: OK")

    def _insert_habilitations(self):
        self._success("Ajout des habilitations dans Metabase")
        for habilitation in ImpactHabilitation.objects.all():
            # https://docs.djangoproject.com/fr/4.2/topics/db/optimization/#use-foreign-key-values-directly
            meta_h = MetabaseHabilitation.objects.create(
                impact_id=habilitation.pk,
                utilisateur=MetabaseUtilisateur.objects.get(
                    impact_id=habilitation.user_id
                ),
                entreprise=MetabaseEntreprise.objects.get(
                    impact_id=habilitation.entreprise_id
                ),
                fonctions=habilitation.fonctions,
                confirmee_le=habilitation.confirmed_at,
            )
            self._success(str(habilitation.pk))
        self._success("Ajout des habilitations dans Metabase: OK")

    def _success(self, message):
        self.stdout.write(self.style.SUCCESS(message))


def _last_update(entreprise):
    last_update = entreprise.updated_at
    for caracteristiques in CaracteristiquesAnnuelles.objects.filter(
        entreprise=entreprise
    ):
        if caracteristiques.updated_at > last_update:
            last_update = caracteristiques.updated_at
    return last_update
