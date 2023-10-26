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
            caracteristiques = (
                entreprise.dernieres_caracteristiques_qualifiantes
                or entreprise.dernieres_caracteristiques
            )
            meta_e = MetabaseEntreprise.objects.create(
                impact_id=entreprise.pk,
                ajoutee_le=entreprise.created_at,
                modifiee_le=_last_update(entreprise),
                siren=entreprise.siren,
                denomination=entreprise.denomination,
                date_cloture_exercice=caracteristiques.date_cloture_exercice
                if caracteristiques
                else None,
                date_derniere_qualification=entreprise.date_derniere_qualification,
                appartient_groupe=entreprise.appartient_groupe,
                societe_mere_en_france=entreprise.societe_mere_en_france,
                comptes_consolides=entreprise.comptes_consolides,
                effectif=caracteristiques.effectif if caracteristiques else None,
                effectif_outre_mer=caracteristiques.effectif_outre_mer
                if caracteristiques
                else None,
                effectif_groupe=caracteristiques.effectif_groupe
                if caracteristiques
                else None,
                tranche_chiffre_affaires=caracteristiques.tranche_chiffre_affaires
                if caracteristiques
                else None,
                tranche_bilan=caracteristiques.tranche_bilan
                if caracteristiques
                else None,
                tranche_chiffre_affaires_consolide=caracteristiques.tranche_chiffre_affaires_consolide
                if caracteristiques
                else None,
                tranche_bilan_consolide=caracteristiques.tranche_bilan_consolide
                if caracteristiques
                else None,
                bdese_accord=caracteristiques.bdese_accord
                if caracteristiques
                else None,
                systeme_management_energie=caracteristiques.systeme_management_energie
                if caracteristiques
                else None,
                nombre_utilisateurs=entreprise.nombre_utilisateurs,
            )
            meta_e.save()
            self._success(str(entreprise))
        self._success("Ajout des entreprises dans Metabase: OK")

    def _insert_utilisateurs(self):
        self._success("Ajout des utilisateurs dans Metabase")
        for utilisateur in ImpactUtilisateur.objects.annotate(
            nombre_entreprises=Count("entreprise")
        ):
            meta_u = MetabaseUtilisateur.objects.create(
                impact_id=utilisateur.pk,
                ajoute_le=utilisateur.created_at,
                modifie_le=utilisateur.updated_at,
                connecte_le=utilisateur.last_login,
                reception_actualites=utilisateur.reception_actualites,
                email_confirme=utilisateur.is_email_confirmed,
                nombre_entreprises=utilisateur.nombre_entreprises,
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
                ajoutee_le=habilitation.created_at,
                modifiee_le=habilitation.updated_at,
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
