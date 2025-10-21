from datetime import date
from time import time
from unittest.mock import patch

import responses
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count
from django.db.models import Max
from django.db.models import Prefetch

from entreprises.models import CaracteristiquesAnnuelles
from entreprises.models import Entreprise as PortailRSEEntreprise
from habilitations.models import Habilitation as PortailRSEHabilitation
from invitations.models import Invitation as PortailRSEInvitation
from metabase.models import BDESE as MetabaseBDESE
from metabase.models import BGES as MetabaseBGES
from metabase.models import CSRD as MetabaseCSRD
from metabase.models import Entreprise as MetabaseEntreprise
from metabase.models import Habilitation as MetabaseHabilitation
from metabase.models import IndexEgaPro as MetabaseIndexEgaPro
from metabase.models import Invitation as MetabaseInvitation
from metabase.models import Reglementation
from metabase.models import Stats as MetabaseStats
from metabase.models import TempBGES
from metabase.models import TempEgaPro
from metabase.models import Utilisateur as MetabaseUtilisateur
from metabase.models import VSME as MetabaseVSME
from reglementations.models.csrd import DocumentAnalyseIA
from reglementations.models.csrd import RapportCSRD
from reglementations.views.base import InsuffisammentQualifieeError
from reglementations.views.base import ReglementationStatus
from reglementations.views.bdese import BDESEReglementation
from reglementations.views.bges import BGESReglementation
from reglementations.views.csrd.csrd import CSRDReglementation
from reglementations.views.index_egapro import IndexEgaproReglementation
from users.models import User as PortailRSEUtilisateur
from vsme.models import EXIGENCES_DE_PUBLICATION
from vsme.models import RapportVSME


def mesure(fonction):
    def wrapper(*args, **kwargs):
        start_time = time()
        resultat = fonction(*args, **kwargs)
        end_time = time()
        if settings.METABASE_DEBUG_SYNC:
            print(
                f"Temps d'exécution de {fonction.__name__} : {end_time - start_time} secondes"
            )
        return resultat

    return wrapper


class Command(BaseCommand):
    help = "Synchronise les données de la base de donnée de prod vers la base de données de Metabase"

    def add_arguments(self, parser):
        parser.add_argument(
            "-e",
            "--entreprises",
            action="store_true",
            help="synchronise les entreprises",
        )
        parser.add_argument(
            "-u",
            "--utilisateurs",
            action="store_true",
            help="synchronise les utilisateurs, les invitations et les habilitations",
        )
        parser.add_argument(
            "-r",
            "--reglementations",
            action="store_true",
            help="synchronise les réglementations",
        )
        parser.add_argument(
            "-s", "--stats", action="store_true", help="synchronise les stats"
        )

    def handle(self, *args, **options):
        if not (
            options["entreprises"]
            or options["utilisateurs"]
            or options["reglementations"]
            or options["stats"]
        ):
            # Quand aucun argument n'est passé, on effectue la synchro entièrement
            options["entreprises"] = True
            options["utilisateurs"] = True
            options["reglementations"] = True
            options["stats"] = True

        if options["entreprises"]:
            self._sync_entreprises()
        if options["utilisateurs"]:
            self._sync_utilisateurs()
            self._sync_invitations()
            self._sync_habilitations()
        if options["reglementations"]:
            self._register_responses()
            self._sync_reglementations()
        if options["stats"]:
            self._insert_stats()

    @mesure
    def _sync_entreprises(self):
        MetabaseEntreprise.objects.all().delete()
        self._success("Suppression des entreprises de Metabase: OK")

        self._success("Ajout des entreprises dans Metabase")
        bulk = []

        for entreprise in PortailRSEEntreprise.objects.prefetch_related(
            Prefetch(
                "caracteristiquesannuelles_set",
                queryset=CaracteristiquesAnnuelles.objects.order_by("-annee"),
                to_attr="caracteristiques",
            )
        ).annotate(nombre_utilisateurs=Count("users")):
            caracteristiques = (
                entreprise.caracteristiques[0] if entreprise.caracteristiques else None
            )
            mb_entreprise = MetabaseEntreprise(
                impact_id=entreprise.pk,
                ajoutee_le=entreprise.created_at,
                modifiee_le=(
                    max(entreprise.updated_at, caracteristiques.updated_at)
                    if caracteristiques
                    else entreprise.updated_at
                ),
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
            bulk.append(mb_entreprise)

        with transaction.atomic():
            MetabaseEntreprise.objects.bulk_create(bulk)

        self._success("Ajout des entreprises dans Metabase: OK")

    @mesure
    def _sync_utilisateurs(self):
        MetabaseUtilisateur.objects.all().delete()
        self._success("Suppression des utilisateurs de Metabase: OK")

        self._success("Ajout des utilisateurs dans Metabase")
        bulk = []
        for utilisateur in PortailRSEUtilisateur.objects.annotate(
            nombre_entreprises=Count("entreprise")
        ):
            mb_utilisateur = MetabaseUtilisateur(
                impact_id=utilisateur.pk,
                ajoute_le=utilisateur.created_at,
                modifie_le=utilisateur.updated_at,
                connecte_le=utilisateur.last_login,
                reception_actualites=utilisateur.reception_actualites,
                email_confirme=utilisateur.is_email_confirmed,
                nombre_entreprises=utilisateur.nombre_entreprises,
            )
            bulk.append(mb_utilisateur)

        with transaction.atomic():
            MetabaseUtilisateur.objects.bulk_create(bulk)

        self._success("Ajout des utilisateurs dans Metabase: OK")

    @mesure
    def _sync_invitations(self):
        MetabaseInvitation.objects.all().delete()
        self._success("Suppression des invitations de Metabase: OK")

        self._success("Ajout des invitations dans Metabase")
        # on ne synchronise que les invitations des entreprises déjà synchronisées dans Metabase pour éviter des problèmes d'intégrité
        bulk = []
        mb_entreprises = list(
            MetabaseEntreprise.objects.values_list("impact_id", flat=True)
        )
        for invitation in PortailRSEInvitation.objects.filter(
            entreprise_id__in=mb_entreprises
        ):
            mb_invitation = MetabaseInvitation(
                impact_id=invitation.pk,
                ajoutee_le=invitation.created_at,
                modifiee_le=invitation.updated_at,
                entreprise_id=invitation.entreprise_id,  # optimisation possible car la clé primaire de l'objet Metabase est identique à la clé primaire dans PortailRSE
                inviteur_id=(
                    invitation.inviteur_id if invitation.inviteur else None
                ),  # optimisation possible car la clé primaire de l'objet Metabase est identique à la clé primaire dans PortailRSE
                role=invitation.role,
                date_acceptation=invitation.date_acceptation,
            )
            bulk.append(mb_invitation)

        with transaction.atomic():
            MetabaseInvitation.objects.bulk_create(bulk)

        self._success("Ajout des invitations dans Metabase: OK")

    @mesure
    def _sync_habilitations(self):
        MetabaseHabilitation.objects.all().delete()
        self._success("Suppression des habilitations de Metabase: OK")

        self._success("Ajout des habilitations dans Metabase")
        # on ne synchronise que les habilitations des entreprises et utilisateurs déjà synchronisés dans Metabase pour éviter des problèmes d'intégrité
        mb_entreprises = list(
            MetabaseEntreprise.objects.values_list("impact_id", flat=True)
        )
        mb_utilisateurs = list(
            MetabaseUtilisateur.objects.values_list("impact_id", flat=True)
        )
        bulk = []
        for habilitation in PortailRSEHabilitation.objects.filter(
            entreprise_id__in=mb_entreprises, user_id__in=mb_utilisateurs
        ):
            # https://docs.djangoproject.com/fr/4.2/topics/db/optimization/#use-foreign-key-values-directly
            mb_habilitation = MetabaseHabilitation(
                impact_id=habilitation.pk,
                ajoutee_le=habilitation.created_at,
                modifiee_le=habilitation.updated_at,
                utilisateur_id=habilitation.user_id,  # optimisation possible car la clé primaire de l'objet Metabase est identique à la clé primaire dans PortailRSE
                entreprise_id=habilitation.entreprise_id,  # optimisation possible car la clé primaire de l'objet Metabase est identique à la clé primaire dans PortailRSE
                fonctions=habilitation.fonctions,
                confirmee_le=habilitation.confirmed_at,
                invitation_id=(
                    habilitation.invitation_id if habilitation.invitation_id else None
                ),  # optimisation possible car la clé primaire de l'objet Metabase est identique à la clé primaire dans PortailRSE
            )
            bulk.append(mb_habilitation)

        with transaction.atomic():
            MetabaseHabilitation.objects.bulk_create(bulk)

        self._success("Ajout des habilitations dans Metabase: OK")

    def _success(self, message):
        self.stdout.write(self.style.SUCCESS(message))

    @mesure
    def _sync_reglementations(self):
        MetabaseVSME.objects.all().delete()
        MetabaseCSRD.objects.all().delete()
        MetabaseBGES.objects.all().delete()
        MetabaseBDESE.objects.all().delete()
        MetabaseIndexEgaPro.objects.all().delete()
        self._success("Suppression des réglementations de Metabase: OK")

        self._success("Ajout des réglementations dans Metabase")
        # on ne synchronise que les réglementations des entreprises déjà synchronisées dans Metabase pour éviter des problèmes d'intégrité
        mb_entreprises = list(
            MetabaseEntreprise.objects.values_list("impact_id", flat=True)
        )
        vsme = []
        csrd = []
        bges = []
        egapro = []
        bdese = []
        for entreprise in (
            PortailRSEEntreprise.objects.filter(users__isnull=False)
            .filter(id__in=mb_entreprises)
            .prefetch_related(
                Prefetch(
                    "caracteristiquesannuelles_set",
                    queryset=CaracteristiquesAnnuelles.objects.order_by("-annee"),
                    to_attr="caracteristiques",
                )
            )
            .distinct()
        ):
            caracteristiques = (
                entreprise.caracteristiques[0] if entreprise.caracteristiques else None
            )
            if caracteristiques:
                if r := self._insert_vsme(caracteristiques):
                    vsme.append(r)

                if r := self._insert_csrd(caracteristiques):
                    csrd.append(r)

                if r := self._insert_bges(caracteristiques):
                    bges.append(r)

                if r := self._insert_bdese(caracteristiques):
                    bdese.append(r)

                if r := self._insert_index_egapro(caracteristiques):
                    egapro.append(r)

        with transaction.atomic():
            if vsme:
                MetabaseVSME.objects.bulk_create(vsme)
            if csrd:
                MetabaseCSRD.objects.bulk_create(csrd)
            if bges:
                MetabaseBGES.objects.bulk_create(bges)
            if bdese:
                MetabaseBDESE.objects.bulk_create(bdese)
            if egapro:
                MetabaseIndexEgaPro.objects.bulk_create(egapro)

        self._success("Ajout des réglementations dans Metabase: OK")

    def _insert_vsme(self, caracteristiques):
        entreprise = caracteristiques.entreprise

        if (
            dernier_rapport := RapportVSME.objects.annotate(
                nb_indicateurs=Count("indicateurs"),
                derniere_modif_indicateur=Max("indicateurs__updated_at"),
            )
            .filter(entreprise_id=entreprise.id)
            .order_by("-annee")
            .first()
        ):
            # On ne synchronise que le dernier rapport actuellement, comme pour la CSRD
            # mais on pourrait vouloir tous les rapports quand il y en a plusieurs
            cree_le = dernier_rapport.created_at
            if dernier_rapport.nb_indicateurs > 0:
                modifie_le = dernier_rapport.derniere_modif_indicateur
                progression = dernier_rapport.progression()["pourcent"]
                progression_par_exigence = {}
                for code, exigence in EXIGENCES_DE_PUBLICATION.items():
                    progression_par_exigence[f"progression_{code}"] = (
                        dernier_rapport.progression_par_exigence(exigence)["pourcent"]
                    )
            else:
                modifie_le = dernier_rapport.updated_at
                progression = 0
                progression_par_exigence = {
                    f"progression_{code}": 0 for code in EXIGENCES_DE_PUBLICATION
                }

            return MetabaseVSME(
                entreprise_id=entreprise.id,  # optimisation possible car la clé primaire de l'objet Metabase est identique à la clé primaire dans PortailRSE
                est_soumise=True,
                statut=(
                    Reglementation.STATUT_EN_COURS
                    if progression < 100
                    else Reglementation.STATUT_A_JOUR
                ),
                cree_le=cree_le,
                modifie_le=modifie_le,
                nb_indicateurs_completes=dernier_rapport.nb_indicateurs,
                progression=progression,
                **progression_par_exigence,
            )
        else:
            return

    def _insert_csrd(self, caracteristiques):
        entreprise = caracteristiques.entreprise
        result = None
        if "csrd" in settings.METABASE_DEBUG_SKIP_STEPS:
            return
        try:
            est_soumise = CSRDReglementation.est_soumis(caracteristiques)
        except InsuffisammentQualifieeError:
            return
        if est_soumise:
            portail_rse_status = CSRDReglementation.calculate_status(
                caracteristiques
            ).status
            statut = self._convertit_portail_rse_status_en_statut_metabase(
                portail_rse_status
            )
            champs = {
                "entreprise_id": entreprise.id,  # optimisation possible car la clé primaire de l'objet Metabase est identique à la clé primaire dans PortailRSE
                "est_soumise": est_soumise,
                "statut": statut,
            }
            # spécificités rapport CSRD
            if (
                dernier_rapport := RapportCSRD.objects.prefetch_related("enjeux")
                .filter(entreprise_id=entreprise.id)
                .order_by("-annee")
                .first()
            ):
                nb_documents_ia = DocumentAnalyseIA.objects.filter(
                    rapport_csrd=dernier_rapport
                ).count()
                nb_iro_selectionnes = dernier_rapport.enjeux.exclude(
                    materiel=None
                ).count()

                champs |= {
                    "nb_documents_ia": nb_documents_ia,
                    "etape_validee": dernier_rapport.etape_validee,
                    "lien_rapport": dernier_rapport.lien_rapport != "",
                    "nb_iro_selectionnes": nb_iro_selectionnes,
                }
            result = MetabaseCSRD(**champs)
        else:
            result = MetabaseCSRD(
                entreprise=MetabaseEntreprise.objects.get(impact_id=entreprise.id),
                est_soumise=est_soumise,
            )

        return result

    def _insert_bdese(self, caracteristiques):
        entreprise = caracteristiques.entreprise
        result = None
        if "bdese" in settings.METABASE_DEBUG_SKIP_STEPS:
            return
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
            result = MetabaseBDESE(
                entreprise_id=entreprise.id,  # optimisation possible car la clé primaire de l'objet Metabase est identique à la clé primaire dans PortailRSE
                est_soumise=est_soumise,
                statut=statut,
            )
        else:
            result = MetabaseBDESE(
                entreprise_id=entreprise.id,  # optimisation possible car la clé primaire de l'objet Metabase est identique à la clé primaire dans PortailRSE
                est_soumise=est_soumise,
            )

        return result

    @responses.activate
    def _insert_index_egapro(self, caracteristiques):
        # des appels API sont nécessaires pour calculate_status() : utilisation de tables de travail
        entreprise = caracteristiques.entreprise
        result = None
        if "egapro" in settings.METABASE_DEBUG_SKIP_STEPS:
            return
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

        result = MetabaseIndexEgaPro(
            entreprise_id=entreprise.id,  # optimisation possible car la clé primaire de l'objet Metabase est identique à la clé primaire dans PortailRSE
            est_soumise=est_soumise,
            statut=statut,
        )

        return result

    @responses.activate
    def _insert_bges(self, caracteristiques):
        # des appels API sont nécessaires pour calculate_status() : utilisation de tables de travail
        entreprise = caracteristiques.entreprise
        result = None
        if "bges" in settings.METABASE_DEBUG_SKIP_STEPS:
            return
        try:
            est_soumise = BGESReglementation.est_soumis(caracteristiques)
        except InsuffisammentQualifieeError:
            return
        if est_soumise:
            with patch(
                "api.bges.extract_last_reporting_year",
                _mock_extract_last_reporting_year,
            ):
                portail_rse_status = BGESReglementation.calculate_status(
                    caracteristiques
                ).status
                statut = self._convertit_portail_rse_status_en_statut_metabase(
                    portail_rse_status
                )
        else:
            statut = None

        result = MetabaseBGES(
            entreprise_id=entreprise.id,  # optimisation possible car la clé primaire de l'objet Metabase est identique à la clé primaire dans PortailRSE
            entreprise=MetabaseEntreprise.objects.get(impact_id=entreprise.id),
            est_soumise=est_soumise,
            statut=statut,
        )

        return result

    def _convertit_portail_rse_status_en_statut_metabase(self, portail_rse_status):
        match portail_rse_status:
            case ReglementationStatus.STATUS_A_ACTUALISER:
                return Reglementation.STATUT_A_ACTUALISER
            case ReglementationStatus.STATUS_EN_COURS:
                return Reglementation.STATUT_EN_COURS
            # FIXME: ce point métier est à confirmer !
            case (
                ReglementationStatus.STATUS_A_JOUR | ReglementationStatus.STATUS_SOUMIS
            ):
                return Reglementation.STATUT_A_JOUR
            case _:
                return f"?{portail_rse_status}?"

    @mesure
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

    def _register_responses(self):
        # permet de mocker efficacement les appels à requests en utilisant les tables de travail
        self.stdout.write(
            self.style.WARNING(
                " > utilisation des tables temporaires pour BGES et EgaPro"
            )
        )

        # mocks responses pour EgaPro
        responses.add_callback(
            method="GET",
            url=r"^https://egapro.travail.gouv.fr/api/public/declaration/",
            callback=callback_egapro,
        )

        # mocks responses pour BGES
        responses.add_callback(
            method="GET",
            url="https://bilans-ges.ademe.fr/api/inventories",
            callback=callback_bges,
        )


# Callbacks pour `responses`


def callback_egapro(request):
    # mock de l'API EgaPro avec les valeurs pré-enregistrées de TempEgaPro
    params = request.url.split("/")
    siren = params[-2]
    annee = params[-1]
    try:
        temp_egapro = TempEgaPro.objects.get(siren=siren, annee=annee)
        return temp_egapro.reponse_api
    except TempEgaPro.DoesNotExist:
        return None


def callback_bges(request):
    # completement fake, mais permet de ne pas toucher le code existant.
    # a utiliser conjointement avec un mock de `extract_last_reporting_year()`
    siren = request.params.get("entity.siren")
    if siren:
        latest_publication = (
            TempBGES.objects.filter(siren=siren).order_by("-dt_publication").first()
        )
        if latest_publication:
            return (200, {}, {"annee": latest_publication.dt_publication.year})
    return (404, {}, {})


# mock pour les appels BGES : uniquement actif dans cette management command


def _mock_extract_last_reporting_year(json_data):
    return json_data["annee"]
