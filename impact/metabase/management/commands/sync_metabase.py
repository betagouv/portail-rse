from datetime import date

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from django.db.models import Count

from entreprises.models import CaracteristiquesAnnuelles
from entreprises.models import Entreprise as PortailRSEEntreprise
from habilitations.models import Habilitation as PortailRSEHabilitation
from invitations.models import Invitation as PortailRSEInvitation
from metabase.models import BDESE as MetabaseBDESE
from metabase.models import BGES as MetabaseBGES
from metabase.models import Entreprise as MetabaseEntreprise
from metabase.models import Habilitation as MetabaseHabilitation
from metabase.models import IndexEgaPro as MetabaseIndexEgaPro
from metabase.models import Invitation as MetabaseInvitation
from metabase.models import Stats as MetabaseStats
from metabase.models import Utilisateur as MetabaseUtilisateur
from reglementations.views.base import InsuffisammentQualifieeError
from reglementations.views.base import ReglementationStatus
from reglementations.views.bdese import BDESEReglementation
from reglementations.views.bges import BGESReglementation
from reglementations.views.index_egapro import IndexEgaproReglementation
from users.models import User as PortailRSEUtilisateur


class Command(BaseCommand):
    def handle(self, *args, **options):
        self._drop_tables()
        self._insert_entreprises()
        self._insert_utilisateurs()
        self._insert_invitations()
        self._insert_habilitations()
        self._insert_reglementations()
        self._insert_stats()

    def _drop_tables(self):
        MetabaseEntreprise.objects.all().delete()
        self._success("Suppression des entreprises de Metabase: OK")
        MetabaseUtilisateur.objects.all().delete()
        self._success("Suppression des utilisateurs de Metabase: OK")
        MetabaseHabilitation.objects.all().delete()
        self._success("Suppression des habilitations de Metabase: OK")
        MetabaseInvitation.objects.all().delete()
        self._success("Suppression des invitations de Metabase: OK")

    def _insert_entreprises(self):
        self._success("Ajout des entreprises dans Metabase")
        for entreprise in PortailRSEEntreprise.objects.annotate(
            nombre_utilisateurs=Count("users")
        ):
            caracteristiques = (
                entreprise.dernieres_caracteristiques_qualifiantes
                or entreprise.dernieres_caracteristiques
            )
            MetabaseEntreprise.objects.create(
                impact_id=entreprise.pk,
                ajoutee_le=entreprise.created_at,
                modifiee_le=_last_update(entreprise),
                siren=entreprise.siren,
                denomination=entreprise.denomination,
                date_cloture_exercice=(
                    caracteristiques.date_cloture_exercice if caracteristiques else None
                ),
                date_derniere_qualification=entreprise.date_derniere_qualification,
                categorie_juridique=(
                    entreprise.categorie_juridique.name
                    if entreprise.categorie_juridique
                    else None
                ),
                pays=entreprise.pays,
                code_NAF=entreprise.code_NAF,
                est_interet_public=entreprise.est_interet_public,
                est_cotee=entreprise.est_cotee,
                appartient_groupe=entreprise.appartient_groupe,
                est_societe_mere=entreprise.est_societe_mere,
                societe_mere_en_france=entreprise.societe_mere_en_france,
                comptes_consolides=entreprise.comptes_consolides,
                effectif=caracteristiques.effectif if caracteristiques else None,
                effectif_securite_sociale=(
                    caracteristiques.effectif_securite_sociale
                    if caracteristiques
                    else None
                ),
                effectif_outre_mer=(
                    caracteristiques.effectif_outre_mer if caracteristiques else None
                ),
                effectif_groupe=(
                    caracteristiques.effectif_groupe if caracteristiques else None
                ),
                effectif_groupe_france=(
                    caracteristiques.effectif_groupe_france
                    if caracteristiques
                    else None
                ),
                tranche_chiffre_affaires=(
                    caracteristiques.tranche_chiffre_affaires
                    if caracteristiques
                    else None
                ),
                tranche_bilan=(
                    caracteristiques.tranche_bilan if caracteristiques else None
                ),
                tranche_chiffre_affaires_consolide=(
                    caracteristiques.tranche_chiffre_affaires_consolide
                    if caracteristiques
                    else None
                ),
                tranche_bilan_consolide=(
                    caracteristiques.tranche_bilan_consolide
                    if caracteristiques
                    else None
                ),
                bdese_accord=(
                    caracteristiques.bdese_accord if caracteristiques else None
                ),
                systeme_management_energie=(
                    caracteristiques.systeme_management_energie
                    if caracteristiques
                    else None
                ),
                nombre_utilisateurs=entreprise.nombre_utilisateurs,
            )
            self._success(str(entreprise))
        self._success("Ajout des entreprises dans Metabase: OK")

    def _insert_utilisateurs(self):
        self._success("Ajout des utilisateurs dans Metabase")
        for utilisateur in PortailRSEUtilisateur.objects.annotate(
            nombre_entreprises=Count("entreprise")
        ):
            MetabaseUtilisateur.objects.create(
                impact_id=utilisateur.pk,
                ajoute_le=utilisateur.created_at,
                modifie_le=utilisateur.updated_at,
                connecte_le=utilisateur.last_login,
                reception_actualites=utilisateur.reception_actualites,
                email_confirme=utilisateur.is_email_confirmed,
                nombre_entreprises=utilisateur.nombre_entreprises,
            )
            self._success(str(utilisateur.pk))
        self._success("Ajout des utilisateurs dans Metabase: OK")

    def _insert_invitations(self):
        self._success("Ajout des invitations dans Metabase")
        for invitation in PortailRSEInvitation.objects.all():
            MetabaseInvitation.objects.create(
                impact_id=invitation.pk,
                ajoutee_le=invitation.created_at,
                modifiee_le=invitation.updated_at,
                entreprise=MetabaseEntreprise.objects.get(
                    impact_id=invitation.entreprise_id
                ),
                inviteur=(
                    MetabaseUtilisateur.objects.get(impact_id=invitation.inviteur_id)
                    if invitation.inviteur
                    else None
                ),
                role=invitation.role,
                date_acceptation=invitation.date_acceptation,
            )

    def _insert_habilitations(self):
        self._success("Ajout des habilitations dans Metabase")
        for habilitation in PortailRSEHabilitation.objects.all():
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
                invitation=(
                    MetabaseInvitation.objects.get(impact_id=habilitation.invitation_id)
                    if habilitation.invitation_id
                    else None
                ),
            )
            self._success(str(habilitation.pk))
        self._success("Ajout des habilitations dans Metabase: OK")

    def _success(self, message):
        self.stdout.write(self.style.SUCCESS(message))

    def _insert_reglementations(self):
        self._success("Ajout des réglementations dans Metabase")
        for entreprise in PortailRSEEntreprise.objects.filter(
            users__isnull=False
        ).distinct():
            caracteristiques = (
                entreprise.dernieres_caracteristiques_qualifiantes
                or entreprise.dernieres_caracteristiques
            )
            if caracteristiques:
                self._insert_bdese(caracteristiques)
                self._insert_index_egapro(caracteristiques)
                self._insert_bges(caracteristiques)
                self._success(str(entreprise))
        self._success("Ajout des réglementations dans Metabase: OK")

    def _insert_bdese(self, caracteristiques):
        entreprise = caracteristiques.entreprise
        try:
            est_soumise = BDESEReglementation.est_soumis(caracteristiques)
        except InsuffisammentQualifieeError:
            return
        if est_soumise:
            portail_rse_status = BDESEReglementation.calculate_status(
                caracteristiques
            ).status
            statut = self._convertit_portail_rse_status_en_statut_metabase(
                portail_rse_status
            )
            MetabaseBDESE.objects.create(
                entreprise=MetabaseEntreprise.objects.get(impact_id=entreprise.id),
                est_soumise=est_soumise,
                statut=statut,
            )
        else:
            MetabaseBDESE.objects.create(
                entreprise=MetabaseEntreprise.objects.get(impact_id=entreprise.id),
                est_soumise=est_soumise,
            )

    def _insert_index_egapro(self, caracteristiques):
        entreprise = caracteristiques.entreprise
        try:
            est_soumise = IndexEgaproReglementation.est_soumis(caracteristiques)
        except InsuffisammentQualifieeError:
            return
        if est_soumise:
            portail_rse_status = IndexEgaproReglementation.calculate_status(
                caracteristiques
            ).status
            statut = self._convertit_portail_rse_status_en_statut_metabase(
                portail_rse_status
            )
        else:
            statut = None
        MetabaseIndexEgaPro.objects.create(
            entreprise=MetabaseEntreprise.objects.get(impact_id=entreprise.id),
            est_soumise=est_soumise,
            statut=statut,
        )

    def _insert_bges(self, caracteristiques):
        entreprise = caracteristiques.entreprise
        try:
            est_soumise = BGESReglementation.est_soumis(caracteristiques)
        except InsuffisammentQualifieeError:
            return
        if est_soumise:
            portail_rse_status = BGESReglementation.calculate_status(
                caracteristiques
            ).status
            statut = self._convertit_portail_rse_status_en_statut_metabase(
                portail_rse_status
            )
        else:
            statut = None
        MetabaseBGES.objects.create(
            entreprise=MetabaseEntreprise.objects.get(impact_id=entreprise.id),
            est_soumise=est_soumise,
            statut=statut,
        )

    def _convertit_portail_rse_status_en_statut_metabase(self, portail_rse_status):
        statut = None
        if portail_rse_status == ReglementationStatus.STATUS_A_ACTUALISER:
            statut = MetabaseBDESE.STATUT_A_ACTUALISER
        elif portail_rse_status == ReglementationStatus.STATUS_EN_COURS:
            statut = MetabaseBDESE.STATUT_EN_COURS
        elif portail_rse_status == ReglementationStatus.STATUS_A_JOUR:
            statut = MetabaseBDESE.STATUT_A_JOUR
        return statut

    def _insert_stats(self):
        self._success("Ajout des stats dans Metabase")
        bdese_statut_connu = (
            MetabaseBDESE.objects.filter(statut__isnull=False)
            .values("entreprise")
            .distinct()
        )
        nombre_bdese_statut_connu = bdese_statut_connu.count()
        nombre_bdese_a_jour = bdese_statut_connu.filter(
            statut=MetabaseBDESE.STATUT_A_JOUR
        ).count()

        index_egapro_statut_connu = (
            MetabaseIndexEgaPro.objects.filter(statut__isnull=False)
            .values("entreprise")
            .distinct()
        )
        nombre_index_egapro_statut_connu = index_egapro_statut_connu.count()
        nombre_index_egapro_a_jour = index_egapro_statut_connu.filter(
            statut=MetabaseBDESE.STATUT_A_JOUR
        ).count()

        bges_statut_connu = (
            MetabaseBGES.objects.filter(statut__isnull=False)
            .values("entreprise")
            .distinct()
        )
        nombre_bges_statut_connu = bges_statut_connu.count()
        nombre_bges_a_jour = bges_statut_connu.filter(
            statut=MetabaseBDESE.STATUT_A_JOUR
        ).count()

        nombre_reglementations_a_jour = (
            nombre_bdese_a_jour + nombre_index_egapro_a_jour + nombre_bges_a_jour
        )
        nombre_reglementations_statut_connu = (
            nombre_bdese_statut_connu
            + nombre_index_egapro_statut_connu
            + nombre_bges_statut_connu
        )
        try:
            stats = MetabaseStats.objects.get(
                date=date.today(),
            )
            stats.reglementations_a_jour = nombre_reglementations_a_jour
            stats.reglementations_statut_connu = nombre_reglementations_statut_connu
            stats.save()
        except ObjectDoesNotExist:
            MetabaseStats.objects.create(
                date=date.today(),
                reglementations_a_jour=nombre_reglementations_a_jour,
                reglementations_statut_connu=nombre_reglementations_statut_connu,
            )
        self._success("Ajout des stats dans Metabase: OK")


def _last_update(entreprise):
    last_update = entreprise.updated_at
    for caracteristiques in CaracteristiquesAnnuelles.objects.filter(
        entreprise=entreprise
    ):
        if caracteristiques.updated_at > last_update:
            last_update = caracteristiques.updated_at
    return last_update
