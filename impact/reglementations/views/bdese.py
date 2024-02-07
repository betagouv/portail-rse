from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import HttpResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from weasyprint import CSS
from weasyprint import HTML

from api import egapro
from entreprises.decorators import entreprise_qualifiee_required
from entreprises.exceptions import EntrepriseNonQualifieeError
from entreprises.models import CaracteristiquesAnnuelles
from entreprises.models import Entreprise
from habilitations.models import get_habilitation
from habilitations.models import is_user_attached_to_entreprise
from habilitations.models import is_user_habilited_on_entreprise
from reglementations.forms import bdese_configuration_form_factory
from reglementations.forms import bdese_form_factory
from reglementations.forms import IntroductionDemoForm
from reglementations.models import annees_a_remplir_bdese
from reglementations.models import BDESE_300
from reglementations.models import BDESE_50_300
from reglementations.models import BDESEAvecAccord
from reglementations.models import derniere_annee_a_remplir_bdese
from reglementations.views.base import Reglementation
from reglementations.views.base import ReglementationAction
from reglementations.views.base import ReglementationStatus


class BDESEReglementation(Reglementation):
    TYPE_AVEC_ACCORD = 1
    TYPE_INFERIEUR_300 = 2
    TYPE_INFERIEUR_500 = 3
    TYPE_SUPERIEUR_500 = 4

    title = "Base de données économiques, sociales et environnementales (BDESE)"
    description = """L'employeur d'au moins 50 salariés doit mettre à disposition du comité économique et social (CSE) ou des représentants du personnel une base de données économiques, sociales et environnementales (BDESE).
        La BDESE rassemble les informations sur les grandes orientations économiques et sociales de l'entreprise.
        En l'absence d'accord d'entreprise spécifique, elle comprend des mentions obligatoires qui varient selon l'effectif de l'entreprise."""
    more_info_url = reverse_lazy("reglementations:fiche_bdese")
    tag = "tag-social"
    summary = "Constituer une base de données économiques, sociales et environnementale sà transmettre à son CSE."

    @classmethod
    def bdese_type(cls, caracteristiques: CaracteristiquesAnnuelles) -> int:
        effectif = caracteristiques.effectif
        if caracteristiques.bdese_accord:
            return cls.TYPE_AVEC_ACCORD
        elif effectif in (
            CaracteristiquesAnnuelles.EFFECTIF_ENTRE_50_ET_249,
            CaracteristiquesAnnuelles.EFFECTIF_ENTRE_250_ET_299,
        ):
            return cls.TYPE_INFERIEUR_300
        elif effectif == CaracteristiquesAnnuelles.EFFECTIF_ENTRE_300_ET_499:
            return cls.TYPE_INFERIEUR_500
        elif effectif in (
            CaracteristiquesAnnuelles.EFFECTIF_ENTRE_500_ET_4999,
            CaracteristiquesAnnuelles.EFFECTIF_ENTRE_5000_ET_9999,
            CaracteristiquesAnnuelles.EFFECTIF_10000_ET_PLUS,
        ):
            return cls.TYPE_SUPERIEUR_500

    @classmethod
    def est_suffisamment_qualifiee(cls, caracteristiques):
        return caracteristiques.effectif is not None

    @staticmethod
    def criteres_remplis(caracteristiques):
        criteres = []
        if caracteristiques.effectif != CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50:
            criteres.append("votre effectif est supérieur à 50 salariés")
        return criteres

    @classmethod
    def est_soumis(cls, caracteristiques):
        super().est_soumis(caracteristiques)
        return (
            caracteristiques.effectif != CaracteristiquesAnnuelles.EFFECTIF_MOINS_DE_50
        )

    @classmethod
    def calculate_status(
        cls,
        caracteristiques: CaracteristiquesAnnuelles,
        user: settings.AUTH_USER_MODEL,
    ) -> ReglementationStatus:
        if reglementation_status := super().calculate_status(caracteristiques, user):
            return reglementation_status

        for match in [
            cls._match_non_soumis,
            cls._match_avec_accord,
            cls._match_bdese_existante,
            cls._match_sans_bdese,
        ]:
            if reglementation_status := match(caracteristiques, user):
                return reglementation_status

    @classmethod
    def _match_non_soumis(cls, caracteristiques, user):
        if not cls.est_soumis(caracteristiques):
            status = ReglementationStatus.STATUS_NON_SOUMIS
            status_detail = "Vous n'êtes pas soumis à cette réglementation."
            entreprise = caracteristiques.entreprise
            annee = derniere_annee_a_remplir_bdese()
            primary_action = ReglementationAction(
                reverse_lazy(
                    "reglementations:bdese_step",
                    args=[entreprise.siren, annee, 1],
                ),
                "Tester une BDESE",
            )
            return ReglementationStatus(
                status, status_detail, primary_action=primary_action
            )

    @classmethod
    def _match_avec_accord(cls, caracteristiques, user):
        if cls.bdese_type(caracteristiques) == cls.TYPE_AVEC_ACCORD:
            annee = derniere_annee_a_remplir_bdese()
            entreprise = caracteristiques.entreprise
            bdese = cls._select_bdese(BDESEAvecAccord, annee, entreprise, user)
            if bdese and bdese.is_complete:
                status = ReglementationStatus.STATUS_A_JOUR
                primary_action_title = f"Marquer ma BDESE {annee} comme non actualisée"
            else:
                status = ReglementationStatus.STATUS_A_ACTUALISER
                primary_action_title = f"Marquer ma BDESE {annee} comme actualisée"

            status_detail = f"Vous êtes soumis à cette réglementation car {', '.join(cls.criteres_remplis(caracteristiques))}. Vous avez un accord d'entreprise spécifique. Veuillez vous y référer."
            primary_action = ReglementationAction(
                reverse_lazy(
                    "reglementations:toggle_bdese_completion",
                    args=[entreprise.siren, annee],
                ),
                primary_action_title,
            )
            return ReglementationStatus(
                status,
                status_detail,
                primary_action=primary_action,
            )

    @classmethod
    def _match_bdese_existante(cls, caracteristiques, user):
        if cls.bdese_type(caracteristiques) == cls.TYPE_INFERIEUR_300:
            bdese_class = BDESE_50_300
        else:
            bdese_class = BDESE_300

        annee = derniere_annee_a_remplir_bdese()
        entreprise = caracteristiques.entreprise
        bdese = cls._select_bdese(bdese_class, annee, entreprise, user)
        if not bdese:
            return

        if bdese.is_complete:
            status = ReglementationStatus.STATUS_A_JOUR
            status_detail = f"Vous êtes soumis à cette réglementation car votre effectif est supérieur à 50 salariés. Vous avez actualisé votre BDESE {annee} sur la plateforme."
            primary_action = ReglementationAction(
                reverse_lazy(
                    "reglementations:bdese_pdf",
                    args=[entreprise.siren, annee],
                ),
                f"Télécharger le pdf {annee}",
                external=True,
            )
            secondary_actions = [
                ReglementationAction(
                    reverse_lazy(
                        "reglementations:bdese_step",
                        args=[entreprise.siren, annee, 1],
                    ),
                    "Modifier ma BDESE",
                )
            ]
        else:
            status = ReglementationStatus.STATUS_EN_COURS
            status_detail = f"Vous êtes soumis à cette réglementation car votre effectif est supérieur à 50 salariés. Vous avez démarré le remplissage de votre BDESE {annee} sur la plateforme."
            primary_action = ReglementationAction(
                reverse_lazy(
                    "reglementations:bdese_step",
                    args=[entreprise.siren, annee, 1],
                ),
                "Reprendre l'actualisation de ma BDESE",
            )
            secondary_actions = [
                ReglementationAction(
                    reverse_lazy(
                        "reglementations:bdese_pdf",
                        args=[entreprise.siren, annee],
                    ),
                    f"Télécharger le pdf {annee} (brouillon)",
                    external=True,
                ),
            ]

        return ReglementationStatus(
            status,
            status_detail,
            primary_action=primary_action,
            secondary_actions=secondary_actions,
        )

    @classmethod
    def _match_sans_bdese(cls, caracteristiques, user):
        annee = derniere_annee_a_remplir_bdese()
        status = ReglementationStatus.STATUS_A_ACTUALISER
        status_detail = "Vous êtes soumis à cette réglementation car votre effectif est supérieur à 50 salariés. Nous allons vous aider à la remplir."
        primary_action = ReglementationAction(
            reverse_lazy(
                "reglementations:bdese_step",
                args=[caracteristiques.entreprise.siren, annee, 0],
            ),
            "Actualiser ma BDESE",
        )
        secondary_actions = []
        return ReglementationStatus(
            status,
            status_detail,
            primary_action=primary_action,
            secondary_actions=secondary_actions,
        )

    @staticmethod
    def _select_bdese(bdese_class, annee, entreprise, user):
        if (
            user
            and is_user_attached_to_entreprise(user, entreprise)
            and not is_user_habilited_on_entreprise(user, entreprise)
        ):
            bdese = bdese_class.personals.filter(
                entreprise=entreprise, annee=annee, user=user
            )
        else:
            bdese = bdese_class.officials.filter(entreprise=entreprise, annee=annee)

        return bdese[0] if bdese else None


@login_required
@entreprise_qualifiee_required
def bdese_pdf(request, siren, annee):
    entreprise = Entreprise.objects.get(siren=siren)
    if not is_user_attached_to_entreprise(request.user, entreprise):
        raise PermissionDenied

    bdese = get_or_create_bdese(entreprise, annee, request.user)

    if bdese.is_bdese_avec_accord:
        raise Http404

    pdf_html = render_bdese_pdf_html(bdese)
    html = HTML(string=pdf_html)
    css = CSS(
        string="""
        @font-face {
            font-family: 'Marianne';
            src: url('../../static/fonts/Marianne/fontes desktop/Marianne-Regular.otf');
        }
        @page {
            font-family: 'Marianne';
        }
        body {
            font-family: 'Marianne';
        }
    """
    )
    pdf_file = html.write_pdf(stylesheets=[css])

    response = HttpResponse(pdf_file, content_type="application/pdf")
    response["Content-Disposition"] = 'filename="bdese.pdf"'
    return response


def render_bdese_pdf_html(bdese):
    context = {"bdese": bdese}
    template_path = _pdf_template_path_from_bdese(bdese)
    pdf_html = render_to_string(template_path, context)
    return pdf_html


def _pdf_template_path_from_bdese(bdese):
    if bdese.is_bdese_300:
        return "reglementations/bdese_300_pdf.html"
    else:
        return "reglementations/bdese_50_300_pdf.html"


@login_required
@entreprise_qualifiee_required
def bdese_step(request, siren, annee, step):
    entreprise = Entreprise.objects.get(siren=siren)
    if not is_user_attached_to_entreprise(request.user, entreprise):
        raise PermissionDenied

    bdese = get_or_create_bdese(entreprise, annee, request.user)

    if bdese.is_bdese_avec_accord:
        raise Http404
    if not bdese.is_configured and step != 0:
        messages.warning(request, f"Commencez par configurer votre BDESE {annee}")
        return redirect("reglementations:bdese_step", siren=siren, annee=annee, step=0)

    if request.method == "POST":
        if "mark_incomplete" in request.POST:
            bdese.mark_step_as_incomplete(step)
            bdese.save()
            return redirect(
                "reglementations:bdese_step", siren=siren, annee=annee, step=step
            )
        else:
            if step == 0:
                form = bdese_configuration_form_factory(bdese, data=request.POST)
            else:
                form = bdese_form_factory(
                    bdese,
                    step,
                    data=request.POST,
                )
            if form.is_valid():
                bdese = form.save()
                messages.success(request, "Étape enregistrée")
                if "save_complete" in request.POST:
                    bdese.mark_step_as_complete(step)
                    bdese.save()
                    if step < len(bdese.STEPS) - 1:
                        step += 1
                return redirect(
                    "reglementations:bdese_step", siren=siren, annee=annee, step=step
                )
            else:
                messages.error(
                    request,
                    "L'étape n'a pas été enregistrée car le formulaire contient des erreurs",
                )

    else:
        if step == 0:
            initial = None
            if not bdese.is_configured:
                initial = initialize_bdese_configuration(bdese)
            form = bdese_configuration_form_factory(
                bdese,
                initial=initial,
            )
        else:
            fetched_data = egapro.indicateurs_bdese(entreprise.siren, annee)
            form = bdese_form_factory(
                bdese,
                step,
                fetched_data=fetched_data,
            )

    if (
        not is_user_habilited_on_entreprise(request.user, entreprise)
        and entreprise.users.count() >= 2
    ):
        messages.info(
            request,
            "Plusieurs utilisateurs sont liés à cette entreprise. Les informations que vous remplissez ne sont pas partagées avec les autres utilisateurs tant que vous n'êtes pas habilités.",
        )

    return render(
        request,
        _bdese_step_template_path(bdese, step),
        _bdese_step_context(form, entreprise, annee, bdese, step),
    )


def _bdese_step_template_path(bdese: BDESE_300 | BDESE_50_300, step: int) -> str:
    if step == 0:
        directory = ""
        template_file = "0_categories_professionnelles.html"
    else:
        if bdese.is_bdese_300:
            directory = "bdese_300/"
        else:
            directory = "bdese_50_300/"
        templates = {
            1: "1_investissement_social.html",
            2: "2_investissement_matériel_et_immatériel.html",
            3: "3_egalite_professionnelle.html",
            4: "4_fonds_propres_endettement_impots.html",
            5: "5_remuneration.html",
            6: "6_representation_du_personnel_et_activites_sociales_et_culturelles.html",
            7: "7_remuneration_des_financeurs.html",
            8: "8_flux_financiers.html",
            9: "9_partenariats.html",
            10: "10_transferts_commerciaux_et_financiers.html",
            11: "11_environnement.html",
        }
        template_file = templates[step]
    return f"reglementations/{directory}{template_file}"


def _bdese_step_context(form, entreprise, annee, bdese, step):
    steps = {
        step: {
            "name": bdese.STEPS[step],
            "is_complete": bdese.step_is_complete(step),
        }
        for step in bdese.STEPS
    }
    step_is_complete = steps[step]["is_complete"]
    bdese_is_complete = bdese.is_complete
    context = {
        "form": form,
        "siren": entreprise.siren,
        "annee": annee,
        "step_is_complete": step_is_complete,
        "steps": steps,
        "bdese_is_complete": bdese_is_complete,
        "annees": annees_a_remplir_bdese(),
        "est_soumis_actuellement": BDESEReglementation.est_soumis(
            entreprise.dernieres_caracteristiques_qualifiantes
        ),
    }
    if step == 0:
        context["demo_form"] = IntroductionDemoForm()
    return context


def get_or_create_bdese(
    entreprise: Entreprise,
    annee: int,
    user: settings.AUTH_USER_MODEL,
) -> BDESE_300 | BDESE_50_300 | BDESEAvecAccord:
    caracteristiques = entreprise.dernieres_caracteristiques_qualifiantes
    if not caracteristiques:
        raise EntrepriseNonQualifieeError(
            "Veuillez renseigner les informations suivantes pour accéder à la BDESE",
            entreprise,
        )

    bdese_type = BDESEReglementation.bdese_type(caracteristiques)
    habilitation = get_habilitation(user, entreprise)
    if bdese_type == BDESEReglementation.TYPE_AVEC_ACCORD:
        bdese_class = BDESEAvecAccord
    elif bdese_type in (
        BDESEReglementation.TYPE_INFERIEUR_500,
        BDESEReglementation.TYPE_SUPERIEUR_500,
    ):
        bdese_class = BDESE_300
    else:
        bdese_class = BDESE_50_300

    if habilitation.is_confirmed:
        bdese, _ = bdese_class.officials.get_or_create(
            entreprise=entreprise, annee=annee
        )
    else:
        bdese, _ = bdese_class.personals.get_or_create(
            entreprise=entreprise, annee=annee, user=user
        )

    return bdese


def initialize_bdese_configuration(bdese: BDESE_300 | BDESE_50_300) -> dict:
    bdeses = bdese.__class__.objects.filter(
        entreprise=bdese.entreprise, user=bdese.user
    ).order_by("-annee")
    for _bdese in bdeses:
        if _bdese.categories_professionnelles:
            initial = {
                "categories_professionnelles": _bdese.categories_professionnelles
            }
            if _bdese.is_bdese_300:
                initial[
                    "categories_professionnelles_detaillees"
                ] = _bdese.categories_professionnelles_detaillees
                initial["niveaux_hierarchiques"] = _bdese.niveaux_hierarchiques
            return initial


@login_required
@entreprise_qualifiee_required
def toggle_bdese_completion(request, siren, annee):
    entreprise = Entreprise.objects.get(siren=siren)
    if not is_user_attached_to_entreprise(request.user, entreprise):
        raise PermissionDenied

    bdese = get_or_create_bdese(entreprise, annee, request.user)

    if bdese.is_bdese_avec_accord:
        bdese.toggle_completion()
        bdese.save()
        if bdese.is_complete:
            success_message = "La BDESE a été marquée comme actualisée"
        else:
            success_message = "La BDESE a été marquée comme non actualisée"
        messages.success(request, success_message)
    return redirect("reglementations:tableau_de_bord", siren=bdese.entreprise.siren)
