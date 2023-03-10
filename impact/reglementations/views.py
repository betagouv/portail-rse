from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, HttpResponse, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from weasyprint import CSS, HTML

from entreprises.models import Entreprise
from habilitations.models import get_habilitation
from public.forms import EligibiliteForm
from .models import (
    derniere_annee_a_remplir_index_egapro,
    derniere_annee_a_remplir_bdese,
    annees_a_remplir_bdese,
    BDESE_300,
    BDESE_50_300,
)
from .forms import (
    bdese_form_factory,
    bdese_configuration_form_factory,
    IntroductionDemoForm,
)


@dataclass
class ReglementationAction:
    url: str
    title: str
    external: bool = False


@dataclass
class ReglementationStatus:
    STATUS_A_JOUR = "à jour"
    STATUS_A_ACTUALISER = "à actualiser"
    STATUS_EN_COURS = "en cours"
    STATUS_NON_SOUMIS = "non soumis"

    status: str
    status_detail: str
    primary_action: ReglementationAction | None = None
    secondary_actions: list[ReglementationAction] = field(default_factory=list)

    @property
    def is_soumis(self):
        return self.status and self.status != self.STATUS_NON_SOUMIS


class Reglementation(ABC):
    title: str
    description: str
    more_info_url: str

    @classmethod
    @abstractmethod
    def calculate_status(
        cls,
        entreprise: Entreprise,
        annee: int,
        user: settings.AUTH_USER_MODEL = None,
    ) -> ReglementationStatus:
        pass

    @classmethod
    def info(cls):
        return {
            "title": cls.title,
            "description": cls.description,
            "more_info_url": cls.more_info_url,
        }


@dataclass
class BDESEReglementation(Reglementation):
    TYPE_NON_SOUMIS = 0
    TYPE_AVEC_ACCORD = 1
    TYPE_INFERIEUR_300 = 2
    TYPE_INFERIEUR_500 = 3
    TYPE_SUPERIEUR_500 = 4

    title = "Base de données économiques, sociales et environnementales (BDESE)"
    description = """L'employeur d'au moins 50 salariés doit mettre à disposition du comité économique et social (CSE) ou des représentants du personnel une base de données économiques, sociales et environnementales (BDESE).
        La BDESE rassemble les informations sur les grandes orientations économiques et sociales de l'entreprise.
        Elle comprend des mentions obligatoires qui varient selon l'effectif de l'entreprise."""
    more_info_url = "https://entreprendre.service-public.fr/vosdroits/F32193"

    @classmethod
    def bdese_type(cls, entreprise: Entreprise) -> int:
        if entreprise.effectif == "petit":
            return cls.TYPE_NON_SOUMIS
        elif entreprise.bdese_accord:
            return cls.TYPE_AVEC_ACCORD
        elif entreprise.effectif == "moyen":
            return cls.TYPE_INFERIEUR_300
        elif entreprise.effectif == "grand":
            return cls.TYPE_INFERIEUR_500
        else:
            return cls.TYPE_SUPERIEUR_500

    @classmethod
    def calculate_status(
        cls, entreprise: Entreprise, annee: int, user: settings.AUTH_USER_MODEL = None
    ) -> ReglementationStatus:
        if entreprise.effectif == "petit":
            status = ReglementationStatus.STATUS_NON_SOUMIS
            status_detail = "Vous n'êtes pas soumis à cette réglementation"
            return ReglementationStatus(status, status_detail)
        elif entreprise.bdese_accord:
            status = ReglementationStatus.STATUS_A_ACTUALISER
            status_detail = "Vous êtes soumis à cette réglementation. Vous avez un accord d'entreprise spécifique. Veuillez vous y référer."
            primary_action = ReglementationAction(
                "#", "Marquer ma BDESE comme actualisée"
            )
            return ReglementationStatus(
                status,
                status_detail,
                primary_action=primary_action,
            )
        else:
            if entreprise.effectif == "moyen":
                bdese_class = BDESE_50_300
            else:
                bdese_class = BDESE_300

            bdese = bdese_class.officials.filter(entreprise=entreprise, annee=annee)
            if (
                user
                and (habilitation := get_habilitation(entreprise, user))
                and not habilitation.is_confirmed
            ):
                bdese = bdese_class.personals.filter(
                    entreprise=entreprise, annee=annee, user=user
                )
            if bdese:
                bdese = bdese[0]
                if bdese.is_complete:
                    status = ReglementationStatus.STATUS_A_JOUR
                    status_detail = "Vous êtes soumis à cette réglementation. Vous avez actualisé votre BDESE sur la plateforme."
                    primary_action = ReglementationAction(
                        reverse_lazy("bdese_pdf", args=[entreprise.siren, annee]),
                        "Télécharger le pdf",
                        external=True,
                    )
                    secondary_actions = [
                        ReglementationAction(
                            reverse_lazy("bdese", args=[entreprise.siren, annee, 1]),
                            "Modifier ma BDESE",
                        )
                    ]
                else:
                    status = ReglementationStatus.STATUS_EN_COURS
                    status_detail = "Vous êtes soumis à cette réglementation. Vous avez démarré le remplissage de votre BDESE sur la plateforme."
                    primary_action = ReglementationAction(
                        reverse_lazy("bdese", args=[entreprise.siren, annee, 1]),
                        "Reprendre l'actualisation de ma BDESE",
                    )
                    secondary_actions = [
                        ReglementationAction(
                            reverse_lazy("bdese_pdf", args=[entreprise.siren, annee]),
                            "Télécharger le pdf (brouillon)",
                            external=True,
                        ),
                    ]
            else:
                status = ReglementationStatus.STATUS_A_ACTUALISER
                status_detail = "Vous êtes soumis à cette réglementation. Nous allons vous aider à la remplir."
                primary_action = ReglementationAction(
                    reverse_lazy("bdese", args=[entreprise.siren, annee, 0]),
                    "Actualiser ma BDESE",
                )
                secondary_actions = []

            return ReglementationStatus(
                status,
                status_detail,
                primary_action=primary_action,
                secondary_actions=secondary_actions,
            )


class IndexEgaproReglementation(Reglementation):
    title = "Index de l’égalité professionnelle"
    description = "Afin de lutter contre les inégalités salariales entre les femmes et les hommes, certaines entreprises doivent calculer et transmettre un index mesurant l’égalité salariale au sein de leur structure."
    more_info_url = "https://www.economie.gouv.fr/entreprises/index-egalite-professionnelle-obligatoire"

    @classmethod
    def calculate_status(
        cls, entreprise: Entreprise, annee: int, user: settings.AUTH_USER_MODEL = None
    ) -> ReglementationStatus:
        PRIMARY_ACTION = ReglementationAction(
            "https://egapro.travail.gouv.fr/",
            "Calculer et déclarer mon index sur Egapro",
            external=True,
        )
        if entreprise.effectif == "petit":
            status = ReglementationStatus.STATUS_NON_SOUMIS
            status_detail = "Vous n'êtes pas soumis à cette réglementation"
        elif is_index_egapro_updated(entreprise):
            status = ReglementationStatus.STATUS_A_JOUR
            status_detail = "Vous êtes soumis à cette réglementation. Vous avez rempli vos obligations d'après les données disponibles sur la plateforme Egapro."
        else:
            status = ReglementationStatus.STATUS_A_ACTUALISER
            status_detail = "Vous êtes soumis à cette réglementation. Vous n'avez pas encore déclaré votre index sur la plateforme Egapro."
        return ReglementationStatus(
            status, status_detail, primary_action=PRIMARY_ACTION
        )


def is_index_egapro_updated(entreprise: Entreprise) -> bool:
    year = derniere_annee_a_remplir_index_egapro()
    url = f"https://egapro.travail.gouv.fr/api/public/declaration/{entreprise.siren}/{year}"
    response = requests.get(url)
    if response.status_code == 200 and "déclaration" in response.json():
        return True
    else:
        return False


def reglementations(request):
    form = EligibiliteForm(request.GET)
    entreprise = None
    if "siren" in form.data:
        if entreprises := Entreprise.objects.filter(siren=form.data["siren"]):
            entreprise = entreprises[0]
            form = EligibiliteForm(request.GET, instance=entreprise)
            commit = (
                request.user.is_authenticated and request.user in entreprise.users.all()
            )
        else:
            commit = True

        if form.is_valid():
            request.session["siren"] = form.cleaned_data["siren"]
            entreprise = form.save(commit=commit)

    return render(
        request,
        "reglementations/reglementations.html",
        _reglementations_context(
            entreprise, request.user if request.user.is_authenticated else None
        ),
    )


@login_required
def reglementation(request, siren):
    entreprise = get_object_or_404(Entreprise, siren=siren)
    if request.user not in entreprise.users.all():
        raise PermissionDenied

    request.session["entreprise"] = entreprise.siren

    return render(
        request,
        "reglementations/reglementations.html",
        _reglementations_context(entreprise, request.user),
    )


def _reglementations_context(entreprise, user):
    reglementations = [
        {
            "info": BDESEReglementation.info(),
            "status": BDESEReglementation.calculate_status(
                entreprise, derniere_annee_a_remplir_bdese(), user
            )
            if entreprise
            else None,
        },
        {
            "info": IndexEgaproReglementation.info(),
            "status": IndexEgaproReglementation.calculate_status(
                entreprise, derniere_annee_a_remplir_index_egapro()
            )
            if entreprise
            else None,
        },
    ]
    return {
        "entreprise": entreprise,
        "reglementations": reglementations,
        "user_manage_entreprise": user in entreprise.users.all()
        if user and entreprise
        else False,
    }


@login_required
def bdese_pdf(request, siren, annee):
    entreprise = Entreprise.objects.get(siren=siren)
    if request.user not in entreprise.users.all():
        raise PermissionDenied
    bdese = _get_or_create_bdese(entreprise, annee, request.user)
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


def get_bdese_data_from_egapro(entreprise: Entreprise, year: int) -> dict:
    EGAPRO_INDICATEURS = {
        "promotions": "Écart taux promotion",
        "augmentations_et_promotions": "Écart taux d'augmentation",
        "rémunérations": "Écart rémunérations",
        "congés_maternité": "Retour congé maternité",
        "hautes_rémunérations": "Hautes rémunérations",
    }

    bdese_data_from_egapro = {
        "nombre_femmes_plus_hautes_remunerations": None,
        "objectifs_progression": None,
    }
    url = f"https://egapro.travail.gouv.fr/api/public/declaration/{entreprise.siren}/{year}"
    response = requests.get(url)

    if response.status_code == 200:
        egapro_data_indicateurs = response.json().get("indicateurs", {})
        if indicateur_hautes_remunerations := egapro_data_indicateurs.get(
            "hautes_rémunérations"
        ):
            bdese_data_from_egapro["nombre_femmes_plus_hautes_remunerations"] = (
                int(indicateur_hautes_remunerations["résultat"])
                if indicateur_hautes_remunerations["population_favorable"] == "hommes"
                else 10 - int(indicateur_hautes_remunerations["résultat"])
            )

        objectifs_progression = {}
        for egapro_indicateur, data in egapro_data_indicateurs.items():
            if objectif := data["objectif_de_progression"]:
                objectifs_progression[EGAPRO_INDICATEURS[egapro_indicateur]] = objectif
        if objectifs_progression:
            bdese_data_from_egapro["objectifs_progression"] = "\n".join(
                f"{egapro_indicateur} : {objectif}"
                for egapro_indicateur, objectif in objectifs_progression.items()
            )
    return bdese_data_from_egapro


@login_required
def bdese(request, siren, annee, step):
    entreprise = Entreprise.objects.get(siren=siren)
    if request.user not in entreprise.users.all():
        raise PermissionDenied

    bdese = _get_or_create_bdese(entreprise, annee, request.user)

    if not bdese.is_configured:
        messages.warning(request, f"Commencez par configurer votre BDESE {annee}")
        return redirect("bdese_configuration", siren=siren, annee=annee)

    if request.method == "POST":
        if "mark_incomplete" in request.POST:
            bdese.mark_step_as_incomplete(step)
            bdese.save()
            return redirect("bdese", siren=siren, annee=annee, step=step)
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
                return redirect("bdese", siren=siren, annee=annee, step=step)
            else:
                messages.error(
                    request,
                    "L'étape n'a pas été enregistrée car le formulaire contient des erreurs",
                )

    else:
        fetched_data = get_bdese_data_from_egapro(entreprise, annee)
        form = bdese_form_factory(
            bdese,
            step,
            fetched_data=fetched_data,
        )

    return render(
        request,
        _bdese_step_template_path(bdese, step),
        _bdese_step_context(form, siren, annee, bdese, step),
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


def _bdese_step_context(form, siren, annee, bdese, step):
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
        "siren": siren,
        "annee": annee,
        "step_is_complete": step_is_complete,
        "steps": steps,
        "bdese_is_complete": bdese_is_complete,
        "annees": annees_a_remplir_bdese(),
    }
    if step == 0:
        context["demo_form"] = IntroductionDemoForm()
    return context


def _get_or_create_bdese(
    entreprise: Entreprise,
    annee: int,
    user: settings.AUTH_USER_MODEL,
) -> BDESE_300 | BDESE_50_300:
    bdese_type = BDESEReglementation.bdese_type(entreprise)
    habilitation = get_habilitation(entreprise, user)
    if bdese_type in (
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


@login_required
def bdese_configuration(request, siren, annee):
    entreprise = Entreprise.objects.get(siren=siren)
    if request.user not in entreprise.users.all():
        raise PermissionDenied

    bdese = _get_or_create_bdese(entreprise, annee, request.user)

    initial = None
    if not bdese.is_configured and not request.POST:
        initial = initialize_bdese_configuration(bdese)

    form = bdese_configuration_form_factory(
        bdese, data=request.POST or None, initial=initial
    )

    if "mark_incomplete" in request.POST:
        bdese.mark_step_as_incomplete(0)
        bdese.save()
        return redirect("bdese", siren=siren, annee=annee, step=0)

    if form.is_valid():
        bdese = form.save()
        messages.success(request, "Catégories enregistrées")
        next_step = 0
        if "save_complete" in request.POST:
            bdese.mark_step_as_complete(0)
            bdese.save()
            next_step = 1
        return redirect("bdese", siren=siren, annee=annee, step=next_step)
    elif request.POST:
        messages.error(
            request,
            "Les catégories n'ont pas été enregistrées car le formulaire contient des erreurs",
        )

    return render(
        request,
        _bdese_step_template_path(bdese, 0),
        _bdese_step_context(form, siren, annee, bdese, 0),
    )


def initialize_bdese_configuration(bdese: BDESE_300 | BDESE_50_300) -> dict:
    bdeses = bdese.__class__.objects.filter(entreprise=bdese.entreprise).order_by(
        "-annee"
    )
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
