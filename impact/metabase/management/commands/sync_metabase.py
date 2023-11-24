from django.core.management.base import BaseCommand
from django.db.models import Count

from entreprises.models import CaracteristiquesAnnuelles
from entreprises.models import Entreprise as ImpactEntreprise
from habilitations.models import Habilitation as ImpactHabilitation
from metabase.models import BDESE as MetabaseBDESE
from metabase.models import Entreprise as MetabaseEntreprise
from metabase.models import Habilitation as MetabaseHabilitation
from metabase.models import IndexEgaPro as MetabaseIndexEgaPro
from metabase.models import Utilisateur as MetabaseUtilisateur
from reglementations.views.base import ReglementationStatus
from reglementations.views.bdese import BDESEReglementation
from reglementations.views.index_egapro import IndexEgaproReglementation
from users.models import User as ImpactUtilisateur


class Command(BaseCommand):
    def handle(self, *args, **options):
        self._drop_tables()
        self._insert_entreprises()
        self._insert_utilisateurs()
        self._insert_habilitations()
        self._insert_reglementations()

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
                categorie_juridique=entreprise.categorie_juridique.name
                if entreprise.categorie_juridique
                else None,
                est_cotee=entreprise.est_cotee,
                appartient_groupe=entreprise.appartient_groupe,
                societe_mere_en_france=entreprise.societe_mere_en_france,
                comptes_consolides=entreprise.comptes_consolides,
                effectif=caracteristiques.effectif if caracteristiques else None,
                effectif_permanent=caracteristiques.effectif_permanent
                if caracteristiques
                else None,
                effectif_outre_mer=caracteristiques.effectif_outre_mer
                if caracteristiques
                else None,
                effectif_groupe=caracteristiques.effectif_groupe
                if caracteristiques
                else None,
                effectif_groupe_permanent=caracteristiques.effectif_groupe_permanent
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

    def _insert_reglementations(self):
        self._insert_bdese()
        self._insert_index_egapro()

    def _insert_bdese(self):
        for entreprise in ImpactEntreprise.objects.filter(
            users__isnull=False
        ).distinct():
            caracteristiques = entreprise.dernieres_caracteristiques_qualifiantes
            if not caracteristiques:
                continue
            est_soumise = BDESEReglementation.est_soumis(caracteristiques)
            if est_soumise:
                for utilisateur in entreprise.users.all():
                    impact_status = BDESEReglementation.calculate_status(
                        caracteristiques, utilisateur
                    ).status
                    if impact_status == ReglementationStatus.STATUS_A_ACTUALISER:
                        statut = MetabaseBDESE.STATUT_A_ACTUALISER
                    elif impact_status == ReglementationStatus.STATUS_EN_COURS:
                        statut = MetabaseBDESE.STATUT_EN_COURS
                    elif impact_status == ReglementationStatus.STATUS_A_JOUR:
                        statut = MetabaseBDESE.STATUT_A_JOUR
                    meta_bdese = MetabaseBDESE.objects.create(
                        entreprise=MetabaseEntreprise.objects.get(
                            impact_id=entreprise.id
                        ),
                        utilisateur=MetabaseUtilisateur.objects.get(
                            impact_id=utilisateur.id
                        ),
                        est_soumise=est_soumise,
                        statut=statut,
                    )
            else:
                meta_bdese = MetabaseBDESE.objects.create(
                    entreprise=MetabaseEntreprise.objects.get(impact_id=entreprise.id),
                    est_soumise=est_soumise,
                )

    def _insert_index_egapro(self):
        for entreprise in ImpactEntreprise.objects.filter(
            users__isnull=False
        ).distinct():
            caracteristiques = entreprise.dernieres_caracteristiques_qualifiantes
            if not caracteristiques:
                continue
            est_soumise = IndexEgaproReglementation.est_soumis(caracteristiques)
            if est_soumise:
                impact_status = IndexEgaproReglementation.calculate_status(
                    caracteristiques, entreprise.users.first()
                ).status
                if impact_status == ReglementationStatus.STATUS_A_ACTUALISER:
                    statut = MetabaseBDESE.STATUT_A_ACTUALISER
                elif impact_status == ReglementationStatus.STATUS_A_JOUR:
                    statut = MetabaseBDESE.STATUT_A_JOUR
            else:
                statut = None
            MetabaseIndexEgaPro.objects.create(
                entreprise=MetabaseEntreprise.objects.get(impact_id=entreprise.id),
                est_soumise=est_soumise,
                statut=statut,
            )


def _last_update(entreprise):
    last_update = entreprise.updated_at
    for caracteristiques in CaracteristiquesAnnuelles.objects.filter(
        entreprise=entreprise
    ):
        if caracteristiques.updated_at > last_update:
            last_update = caracteristiques.updated_at
    return last_update
