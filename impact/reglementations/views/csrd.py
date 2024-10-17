from datetime import datetime
from datetime import timedelta
from functools import wraps
from tempfile import NamedTemporaryFile

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.template.loader import get_template
from django.template.loader import TemplateDoesNotExist
from django.urls import reverse_lazy
from openpyxl import Workbook

from entreprises.models import CaracteristiquesAnnuelles
from entreprises.models import Entreprise
from entreprises.views import get_current_entreprise
from habilitations.models import is_user_attached_to_entreprise
from reglementations.enums import ESRS
from reglementations.models import RapportCSRD
from reglementations.views.base import Reglementation
from reglementations.views.base import ReglementationAction
from reglementations.views.base import ReglementationStatus


class CSRDReglementation(Reglementation):
    title = "Rapport de Durabilité - CSRD"
    more_info_url = reverse_lazy("reglementations:fiche_csrd")
    tag = "tag-durabilite"
    summary = "Publier un rapport de durabilité."
    zone = "europe"

    @classmethod
    def est_suffisamment_qualifiee(cls, caracteristiques):
        return (
            caracteristiques.date_cloture_exercice is not None
            and caracteristiques.entreprise.est_cotee is not None
            and caracteristiques.entreprise.est_interet_public is not None
            and caracteristiques.effectif is not None
            and caracteristiques.tranche_bilan is not None
            and caracteristiques.tranche_chiffre_affaires is not None
            and caracteristiques.entreprise.appartient_groupe is not None
            and (
                not caracteristiques.entreprise.appartient_groupe
                or (
                    caracteristiques.entreprise.comptes_consolides is not None
                    and (
                        not caracteristiques.entreprise.comptes_consolides
                        or (
                            caracteristiques.effectif_groupe is not None
                            and caracteristiques.tranche_bilan_consolide is not None
                            and caracteristiques.tranche_chiffre_affaires_consolide
                            is not None
                        )
                    )
                )
            )
        )

    @classmethod
    def est_soumis(cls, caracteristiques):
        super().est_soumis(caracteristiques)
        return bool(cls.est_soumis_a_partir_de_l_exercice(caracteristiques))

    @classmethod
    def est_soumis_a_partir_de_l_exercice(
        cls, caracteristiques: CaracteristiquesAnnuelles
    ) -> int | None:
        """Le premier exercice pour lequel l'entreprise est soumise à cette réglementation est l'exercice ouvert à compter du 1er janvier de l'année renvoyée"""
        if not (
            cls.critere_categorie_juridique_sirene(caracteristiques)
            or caracteristiques.entreprise.est_interet_public
        ):
            return
        if cls.est_grand_groupe(caracteristiques):
            if caracteristiques.entreprise.est_societe_mere:
                if (
                    caracteristiques.entreprise.est_cotee
                    or caracteristiques.entreprise.est_interet_public
                ) and caracteristiques.effectif_groupe in (
                    CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
                    CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
                    CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
                ):
                    return 2024
                else:
                    return 2025
            else:
                if cls.est_grande_entreprise(caracteristiques):
                    if (
                        caracteristiques.entreprise.est_cotee
                        and caracteristiques.effectif
                        in (
                            CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
                            CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
                            CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
                        )
                    ):
                        return 2024
                    else:
                        return 2025
                elif (
                    caracteristiques.entreprise.est_cotee
                    and cls.est_petite_ou_moyenne_entreprise(caracteristiques)
                ):
                    if caracteristiques.effectif_groupe in (
                        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
                        CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
                        CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
                    ):
                        return 2024
                    else:
                        return 2025
        else:
            if caracteristiques.entreprise.est_dans_EEE:
                if caracteristiques.entreprise.est_cotee:
                    if cls.est_grande_entreprise(caracteristiques):
                        if caracteristiques.effectif in (
                            CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
                            CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
                            CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
                        ):
                            return 2024
                        else:
                            return 2025
                    elif cls.est_petite_ou_moyenne_entreprise(caracteristiques):
                        return 2026
                elif caracteristiques.entreprise.est_interet_public:
                    if cls.est_grande_entreprise(caracteristiques):
                        if caracteristiques.effectif in (
                            CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
                            CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
                            CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
                        ):
                            return 2024
                        else:
                            return 2025
                elif cls.est_grande_entreprise(caracteristiques):
                    return 2025
            else:
                if cls.est_grande_entreprise(caracteristiques):
                    return 2025
                elif (
                    caracteristiques.tranche_chiffre_affaires
                    == CaracteristiquesAnnuelles.CA_100M_ET_PLUS
                ):
                    return 2028

    @classmethod
    def criteres_remplis(cls, caracteristiques):
        criteres = []
        if (
            caracteristiques.entreprise.est_hors_EEE
            and not caracteristiques.entreprise.appartient_groupe
        ):
            criteres.append("votre siège social est hors EEE")
        else:
            if caracteristiques.entreprise.est_cotee:
                criteres.append("votre société est cotée sur un marché réglementé")
            if caracteristiques.entreprise.est_interet_public:
                criteres.append("votre société est d'intérêt public")
            if caracteristiques.entreprise.est_societe_mere and cls.est_grand_groupe(
                caracteristiques
            ):
                criteres.append("votre société est la société mère d'un groupe")
        if critere := cls.critere_effectif(caracteristiques):
            criteres.append(critere)
        if critere := cls.critere_bilan(caracteristiques):
            criteres.append(critere)
        if critere := cls.critere_CA(caracteristiques):
            criteres.append(critere)
        return criteres

    @classmethod
    def critere_effectif(cls, caracteristiques):
        if (
            caracteristiques.entreprise.est_cotee
            or caracteristiques.entreprise.est_interet_public
        ):
            if cls.est_grande_entreprise(caracteristiques):
                if caracteristiques.effectif in (
                    CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
                    CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
                    CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
                ):
                    return "votre effectif est supérieur à 500 salariés"
                elif caracteristiques.effectif in (
                    CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_299,
                    CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499,
                ):
                    return "votre effectif est supérieur à 250 salariés"
            if cls.est_grand_groupe(caracteristiques):
                if caracteristiques.effectif_groupe in (
                    CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
                    CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
                    CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
                ):
                    return "l'effectif du groupe est supérieur à 500 salariés"
                elif (
                    caracteristiques.effectif_groupe
                    == CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_499
                ):
                    return "l'effectif du groupe est supérieur à 250 salariés"
            if cls.est_petite_ou_moyenne_entreprise(caracteristiques):
                if (
                    caracteristiques.effectif
                    != CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10
                ):
                    return "votre effectif est supérieur à 10 salariés"
        else:
            if cls.est_grande_entreprise(caracteristiques):
                if caracteristiques.effectif in (
                    CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_299,
                    CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499,
                    CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
                    CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
                    CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
                ):
                    return "votre effectif est supérieur à 250 salariés"
            if caracteristiques.entreprise.est_societe_mere and cls.est_grand_groupe(
                caracteristiques
            ):
                if caracteristiques.effectif_groupe in (
                    CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_499,
                    CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
                    CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
                    CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
                ):
                    return "l'effectif du groupe est supérieur à 250 salariés"

    @classmethod
    def critere_bilan(cls, caracteristiques):
        if cls.est_grand_groupe(caracteristiques):
            if caracteristiques.tranche_bilan_consolide in (
                CaracteristiquesAnnuelles.BILAN_ENTRE_30M_ET_43M,
                CaracteristiquesAnnuelles.BILAN_ENTRE_43M_ET_100M,
                CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
            ):
                return "le bilan du groupe est supérieur à 30M€"
        if caracteristiques.tranche_bilan in (
            CaracteristiquesAnnuelles.BILAN_ENTRE_25M_ET_43M,
            CaracteristiquesAnnuelles.BILAN_ENTRE_43M_ET_100M,
            CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        ):
            if cls.est_grande_entreprise(caracteristiques):
                return "votre bilan est supérieur à 25M€"
            elif cls.est_petite_ou_moyenne_entreprise(caracteristiques):
                return "votre bilan est supérieur à 450k€"
        elif (
            caracteristiques.tranche_bilan
            == CaracteristiquesAnnuelles.BILAN_ENTRE_450K_ET_25M
        ):
            if cls.est_petite_ou_moyenne_entreprise(caracteristiques):
                return "votre bilan est supérieur à 450k€"

    @classmethod
    def critere_CA(cls, caracteristiques):
        if cls.est_grand_groupe(caracteristiques):
            if caracteristiques.tranche_chiffre_affaires_consolide in (
                CaracteristiquesAnnuelles.CA_ENTRE_60M_ET_100M,
                CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
            ):
                return "le chiffre d'affaires du groupe est supérieur à 60M€"
        if caracteristiques.tranche_chiffre_affaires in (
            CaracteristiquesAnnuelles.CA_ENTRE_50M_ET_100M,
            CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
        ):
            if cls.est_grande_entreprise(caracteristiques):
                return "votre chiffre d'affaires est supérieur à 50M€"
            elif cls.est_petite_ou_moyenne_entreprise(caracteristiques):
                return "votre chiffre d'affaires est supérieur à 900k€"
        elif (
            caracteristiques.tranche_chiffre_affaires
            == CaracteristiquesAnnuelles.CA_ENTRE_900K_ET_50M
        ):
            if cls.est_petite_ou_moyenne_entreprise(caracteristiques):
                return "votre chiffre d'affaires est supérieur à 900k€"

    @classmethod
    def critere_categorie_juridique_sirene(cls, caracteristiques):
        return (
            caracteristiques.entreprise.categorie_juridique_sirene == 3120
            or 5100 <= caracteristiques.entreprise.categorie_juridique_sirene <= 6199
            or 6300 <= caracteristiques.entreprise.categorie_juridique_sirene <= 6499
            or 8100 <= caracteristiques.entreprise.categorie_juridique_sirene <= 8299
        )

    @classmethod
    def est_delegable(cls, caracteristiques):
        if caracteristiques.entreprise.est_societe_mere:
            return False
        elif (
            cls.est_grande_entreprise(caracteristiques)
            and caracteristiques.entreprise.est_cotee
        ):
            return False
        return cls.est_grand_groupe(caracteristiques)

    @classmethod
    def calculate_status(
        cls,
        caracteristiques: CaracteristiquesAnnuelles,
        user: settings.AUTH_USER_MODEL,
    ) -> ReglementationStatus:
        if reglementation_status := super().calculate_status(caracteristiques, user):
            return reglementation_status
        primary_action = ReglementationAction(
            reverse_lazy(
                "reglementations:gestion_csrd",
                kwargs={
                    "siren": caracteristiques.entreprise.siren,
                    "etape": 1,
                },
            ),
            "Accéder à l'espace Rapport de Durabilité",
        )
        if annee := cls.est_soumis_a_partir_de_l_exercice(caracteristiques):
            premiere_annee_publication = (
                cls.decale_annee_publication_selon_cloture_exercice_comptable(
                    annee, caracteristiques
                )
            )
            exercice_comptable = (
                f"{annee}"
                if caracteristiques.exercice_comptable_est_annee_civile
                else f"{annee}-{annee + 1}"
            )
            status_detail = f"Vous êtes soumis à cette réglementation à partir de {premiere_annee_publication} sur les données de l'exercice comptable {exercice_comptable}"
            if annee == 2028:
                # Ce cas ne peut arriver que pour les micro et PME sans groupe hors EEE
                conditions = "votre société dont le siège social est hors EEE revêt une forme juridique comparable aux sociétés par actions ou aux sociétés à responsabilité limitée, comptabilise un chiffre d'affaires net dans l'Espace économique européen qui excède 150 millions d'euros à la date de clôture des deux derniers exercices consécutifs, ne contrôle ni n'est contrôlée par une autre société et dispose d'une succursale en France dont le chiffre d'affaires net excède 40 millions d'euros"
                status_detail += f" si {conditions}."
            else:
                criteres = cls.criteres_remplis(caracteristiques)
                justification = ", ".join(criteres[:-1]) + " et " + criteres[-1]
                status_detail += f" car {justification}."
                if cls.est_delegable(caracteristiques):
                    status_detail += (
                        " Vous pouvez déléguer cette obligation à votre société-mère."
                    )
            status_detail += " Vous devez publier le Rapport de Durabilité en même temps que le rapport de gestion."
            return ReglementationStatus(
                status=ReglementationStatus.STATUS_SOUMIS,
                status_detail=status_detail,
                primary_action=primary_action,
                prochaine_echeance=premiere_annee_publication,
            )
        else:
            return ReglementationStatus(
                status=ReglementationStatus.STATUS_NON_SOUMIS,
                status_detail="Vous n'êtes pas soumis à cette réglementation.",
                primary_action=primary_action,
            )

    @staticmethod
    def decale_annee_publication_selon_cloture_exercice_comptable(
        annee, caracteristiques
    ):
        ouverture_exercice_comptable = (
            caracteristiques.date_cloture_exercice + timedelta(days=1)
        ) + relativedelta(
            year=annee
        )  # remplace l'année de la date d'ouverture de l'exercice comptable par la valeur donnée en paramètre (de manière intelligente pour les années bissextiles)
        cloture_exercice_comptable = (
            ouverture_exercice_comptable + relativedelta(months=+12) - timedelta(days=1)
        )
        return (cloture_exercice_comptable + relativedelta(months=+6)).year

    @classmethod
    def est_microentreprise(cls, caracteristiques: CaracteristiquesAnnuelles):
        nombre_seuils_non_depasses = 0
        if (
            caracteristiques.tranche_bilan
            == CaracteristiquesAnnuelles.BILAN_MOINS_DE_450K
        ):
            nombre_seuils_non_depasses += 1
        if (
            caracteristiques.tranche_chiffre_affaires
            == CaracteristiquesAnnuelles.CA_MOINS_DE_900K
        ):
            nombre_seuils_non_depasses += 1
        if caracteristiques.effectif == CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_10:
            nombre_seuils_non_depasses += 1
        return nombre_seuils_non_depasses >= 2

    @classmethod
    def est_grande_entreprise(cls, caracteristiques: CaracteristiquesAnnuelles) -> bool:
        nombre_seuils_depasses = 0
        if caracteristiques.tranche_bilan in (
            CaracteristiquesAnnuelles.BILAN_ENTRE_25M_ET_43M,
            CaracteristiquesAnnuelles.BILAN_ENTRE_43M_ET_100M,
            CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        ):
            nombre_seuils_depasses += 1
        if caracteristiques.tranche_chiffre_affaires in (
            CaracteristiquesAnnuelles.CA_ENTRE_50M_ET_100M,
            CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
        ):
            nombre_seuils_depasses += 1
        if caracteristiques.effectif in (
            CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_299,
            CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499,
            CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
            CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
            CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        ):
            nombre_seuils_depasses += 1
        return nombre_seuils_depasses >= 2

    @classmethod
    def est_petite_ou_moyenne_entreprise(
        cls, caracteristiques: CaracteristiquesAnnuelles
    ) -> bool:
        return not cls.est_microentreprise(
            caracteristiques
        ) and not cls.est_grande_entreprise(caracteristiques)

    @classmethod
    def est_grand_groupe(cls, caracteristiques: CaracteristiquesAnnuelles) -> bool:
        nombre_seuils_depasses = 0
        if caracteristiques.tranche_bilan_consolide in (
            CaracteristiquesAnnuelles.BILAN_ENTRE_30M_ET_43M,
            CaracteristiquesAnnuelles.BILAN_ENTRE_43M_ET_100M,
            CaracteristiquesAnnuelles.BILAN_100M_ET_PLUS,
        ):
            nombre_seuils_depasses += 1
        if caracteristiques.tranche_chiffre_affaires_consolide in (
            CaracteristiquesAnnuelles.CA_ENTRE_60M_ET_100M,
            CaracteristiquesAnnuelles.CA_100M_ET_PLUS,
        ):
            nombre_seuils_depasses += 1
        if caracteristiques.effectif_groupe in (
            CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_499,
            CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
            CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
            CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        ):
            nombre_seuils_depasses += 1
        return (
            caracteristiques.entreprise.appartient_groupe
            and nombre_seuils_depasses >= 2
        )


@login_required
def guide_csrd(request, siren=None, phase=0, etape=0, sous_etape=0):
    if not siren:
        entreprise = get_current_entreprise(request)
        if not entreprise:
            messages.warning(
                request,
                "Commencez par ajouter une entreprise à votre compte utilisateur avant d'accéder à l'espace Rapport de Durabilité",
            )
            return redirect("entreprises:entreprises")
        return redirect("reglementations:csrd", siren=entreprise.siren)

    entreprise = get_object_or_404(Entreprise, siren=siren)
    if not is_user_attached_to_entreprise(request.user, entreprise):
        raise PermissionDenied

    if sous_etape:
        template_name = (
            f"reglementations/espace_csrd/phase{phase}_etape{etape}_{sous_etape}.html"
        )
    elif etape:
        template_name = f"reglementations/espace_csrd/phase{phase}_etape{etape}.html"
    elif phase:
        template_name = f"reglementations/espace_csrd/phase{phase}.html"
    else:
        template_name = "reglementations/espace_csrd/index.html"

    try:
        template = get_template(template_name)
    except TemplateDoesNotExist:
        raise Http404

    context = {
        "entreprise": entreprise,
        "phase": phase,
        "etape": etape,
        "sous_etape": sous_etape,
    }

    return HttpResponse(template.render(context, request))


@login_required
def gestion_csrd(request, siren=None, etape=1):
    if not siren:
        entreprise = get_current_entreprise(request)
        if not entreprise:
            messages.warning(
                request,
                "Commencez par ajouter une entreprise à votre compte utilisateur avant d'accéder à l'espace Rapport de Durabilité",
            )
            return redirect("entreprises:entreprises")
        return redirect("reglementations:csrd", siren=entreprise.siren)

    entreprise = get_object_or_404(Entreprise, siren=siren)
    if not is_user_attached_to_entreprise(request.user, entreprise):
        raise PermissionDenied

    template_name = f"reglementations/csrd/etape{etape}.html"
    try:
        template = get_template(template_name)
    except TemplateDoesNotExist as e:
        raise Http404

    # En analysant un peu les requêtes exécutées,
    # les fetch sur les habilitations et l'entreprise se répètent (requêtes identiques)
    # un peu de centralisation à faire pour éviter les répétitions dans `utils.middlewares.ExtendUserMiddleware`

    # par ex., on peut récupérer l'habilitation pour cette entreprise, elle est déjà en cache
    habilitation = request.user.habilitation_set.get(entreprise=entreprise)
    annee = datetime.now().year

    # les prefetch de l'enjeu parent évitent des N+1 au niveau du template
    csrd, _ = RapportCSRD.objects.prefetch_related(
        "enjeux", "enjeux__parent"
    ).get_or_create(
        entreprise=entreprise,
        proprietaire=None if habilitation.is_confirmed else request.user,
        annee=annee,
    )

    context = {
        "entreprise": entreprise,
        "etape": etape,
        "csrd": csrd,
        "annee": annee,
        "steps": {
            1: {"name": "Introduction"},
            2: {"name": "Sélection des enjeux"},
            3: {"name": "Matérialité des enjeux"},
        },
    }

    return HttpResponse(template.render(context, request))


def csrd_required(function):
    @wraps(function)
    def wrap(request, siren):
        entreprise = get_object_or_404(Entreprise, siren=siren)
        try:
            habilitation = request.user.habilitation_set.get(entreprise=entreprise)
            csrd = RapportCSRD.objects.prefetch_related("enjeux", "enjeux__parent").get(
                entreprise=entreprise,
                proprietaire=None if habilitation.is_confirmed else request.user,
                annee=datetime.now().year,
            )
            return function(request, siren, csrd=csrd)
        except ObjectDoesNotExist:
            raise Http404("Ce rapport du durabilité n'existe pas")

    return wrap


@login_required
@csrd_required
def enjeux_xlsx(request, siren, csrd=None):
    workbook = Workbook()
    worksheet = workbook.active
    worksheet["A1"] = "ESRS"
    worksheet["B1"] = "Enjeux de durabilité"
    worksheet["C1"] = "Descriptif"
    worksheet["D1"] = "Origine"
    numero_ligne = 2
    for esrs in ESRS:
        enjeux = csrd.enjeux_par_esrs(esrs)
        for enjeu in enjeux:
            if enjeu.selection:
                worksheet[f"A{numero_ligne}"] = enjeu.esrs
                worksheet[f"B{numero_ligne}"] = enjeu.nom
                worksheet[f"C{numero_ligne}"] = enjeu.description
                worksheet[f"D{numero_ligne}"] = (
                    "personnel" if enjeu.modifiable else "AR"
                )
                numero_ligne += 1

    with NamedTemporaryFile() as tmp:
        workbook.save(tmp.name)
        tmp.seek(0)
        xlsx_stream = tmp.read()
    response = HttpResponse(
        xlsx_stream,
        content_type="application/vnd.openxmlformatsofficedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = 'filename="enjeux_csrd.xlsx"'
    return response
