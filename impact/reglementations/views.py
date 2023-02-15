from dataclasses import dataclass, field

import requests
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import HttpResponse, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from weasyprint import CSS, HTML

from entreprises.models import Entreprise
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
class Reglementation:
    STATUS_A_JOUR = "à jour"
    STATUS_A_ACTUALISER = "à actualiser"
    STATUS_EN_COURS = "en cours"
    STATUS_NON_SOUMIS = "non soumis"

    status: str | None = None
    status_detail: str | None = None
    primary_action: ReglementationAction | None = None
    secondary_actions: list[ReglementationAction] = field(default_factory=list)

    @property
    def status_is_soumis(self):
        return self.status and self.status != self.STATUS_NON_SOUMIS


@dataclass
class BDESEReglementation(Reglementation):
    TYPE_AVEC_ACCORD = 1
    TYPE_INFERIEUR_300 = 2
    TYPE_INFERIEUR_500 = 3
    TYPE_SUPERIEUR_500 = 4

    title = "Base de données économiques, sociales et environnementales (BDESE)"
    description = """L'employeur d'au moins 50 salariés doit mettre à disposition du comité économique et social (CSE) ou des représentants du personnel une base de données économiques, sociales et environnementales (BDESE).
        La BDESE rassemble les informations sur les grandes orientations économiques et sociales de l'entreprise.
        Elle comprend des mentions obligatoires qui varient selon l'effectif de l'entreprise."""
    more_info_url = "https://entreprendre.service-public.fr/vosdroits/F32193"

    bdese_type: int | None = None

    @classmethod
    def calculate(cls, entreprise: Entreprise, annee: int) -> "BDESEReglementation":
        if entreprise.effectif == "petit":
            status = cls.STATUS_NON_SOUMIS
            status_detail = "Vous n'êtes pas soumis à cette réglementation"
            return cls(status, status_detail)
        elif entreprise.bdese_accord:
            status = cls.STATUS_A_ACTUALISER
            status_detail = "Vous êtes soumis à cette réglementation. Vous avez un accord d'entreprise spécifique. Veuillez vous y référer."
            primary_action = ReglementationAction(
                "#", "Marquer ma BDESE comme actualisée"
            )
            bdese_type = cls.TYPE_AVEC_ACCORD
            return cls(
                status,
                status_detail,
                primary_action=primary_action,
                bdese_type=bdese_type,
            )
        else:
            if entreprise.effectif == "moyen":
                bdese_type = cls.TYPE_INFERIEUR_300
                bdese_class = BDESE_50_300
            elif entreprise.effectif == "grand":
                bdese_type = cls.TYPE_INFERIEUR_500
                bdese_class = BDESE_300
            else:
                bdese_type = cls.TYPE_SUPERIEUR_500
                bdese_class = BDESE_300

            bdese = bdese_class.objects.filter(
                entreprise__siren=entreprise.siren, annee=annee
            )
            if bdese:
                bdese = bdese[0]
                if bdese.is_complete:
                    status = cls.STATUS_A_JOUR
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
                    status = cls.STATUS_EN_COURS
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
                status = cls.STATUS_A_ACTUALISER
                status_detail = "Vous êtes soumis à cette réglementation. Nous allons vous aider à la remplir."
                primary_action = ReglementationAction(
                    reverse_lazy("bdese", args=[entreprise.siren, annee, 0]),
                    "Actualiser ma BDESE",
                )
                secondary_actions = []

            return cls(
                status,
                status_detail,
                primary_action=primary_action,
                secondary_actions=secondary_actions,
                bdese_type=bdese_type,
            )


@dataclass
class IndexEgaproReglementation(Reglementation):
    title = "Index de l’égalité professionnelle"
    description = "Afin de lutter contre les inégalités salariales entre les femmes et les hommes, certaines entreprises doivent calculer et transmettre un index mesurant l’égalité salariale au sein de leur structure."
    more_info_url = "https://www.economie.gouv.fr/entreprises/index-egalite-professionnelle-obligatoire"

    primary_action: ReglementationAction = ReglementationAction(
        "https://egapro.travail.gouv.fr/",
        "Calculer et déclarer mon index sur Egapro",
        external=True,
    )

    @classmethod
    def calculate(cls, entreprise: Entreprise) -> "IndexEgaproReglementations":
        if entreprise.effectif == "petit":
            status = cls.STATUS_NON_SOUMIS
            status_detail = "Vous n'êtes pas soumis à cette réglementation"
        elif is_index_egapro_updated(entreprise):
            status = cls.STATUS_A_JOUR
            status_detail = "Vous êtes soumis à cette réglementation. Vous avez rempli vos obligations d'après les données disponibles sur la plateforme Egapro."
        else:
            status = cls.STATUS_A_ACTUALISER
            status_detail = "Vous êtes soumis à cette réglementation. Vous n'avez pas encore déclaré votre index sur la plateforme Egapro."
        return cls(status, status_detail)


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
            entreprises = [entreprise]

    else:
        entreprises = (
            request.user.entreprise_set.all()
            if request.user.is_authenticated
            else [None]
        )

    return render(
        request,
        "reglementations/reglementations.html",
        {
            "entreprises": [
                {
                    "entreprise": entreprise,
                    "reglementations": [
                        BDESEReglementation.calculate(
                            entreprise, derniere_annee_a_remplir_bdese()
                        )
                        if entreprise
                        else BDESEReglementation(),
                        IndexEgaproReglementation.calculate(entreprise)
                        if entreprise
                        else IndexEgaproReglementation(),
                    ],
                    "user_manage_entreprise": request.user in entreprise.users.all()
                    if request.user.is_authenticated
                    else False,
                }
                for entreprise in entreprises
            ]
        },
    )


@login_required
def bdese_pdf(request, siren, annee):
    entreprise = Entreprise.objects.get(siren=siren)
    if request.user not in entreprise.users.all():
        raise PermissionDenied
    bdese = _get_or_create_bdese(entreprise, annee)
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
    bdese_data_from_egapro = {}
    url = f"https://egapro.travail.gouv.fr/api/public/declaration/{entreprise.siren}/{year}"
    response = requests.get(url)
    if response.status_code == 200:
        egapro_data = response.json()
        if indicateur_hautes_remunerations := egapro_data.get("indicateurs", {}).get(
            "hautes_rémunérations"
        ):
            bdese_data_from_egapro = {
                "nombre_femmes_plus_hautes_remunerations": int(
                    indicateur_hautes_remunerations["résultat"]
                )
                if indicateur_hautes_remunerations["population_favorable"] == "hommes"
                else 10 - int(indicateur_hautes_remunerations["résultat"])
            }
    return bdese_data_from_egapro


@login_required
def bdese(request, siren, annee, step):
    entreprise = Entreprise.objects.get(siren=siren)
    if request.user not in entreprise.users.all():
        raise PermissionDenied

    bdese = _get_or_create_bdese(entreprise, annee)

    if not bdese.categories_professionnelles:
        messages.warning(
            request, "Commencez par renseigner vos catégories professionnelles"
        )
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
    entreprise: Entreprise, annee: int
) -> BDESE_300 | BDESE_50_300:
    reglementation = BDESEReglementation.calculate(entreprise, annee)
    if reglementation.bdese_type in (
        BDESEReglementation.TYPE_INFERIEUR_500,
        BDESEReglementation.TYPE_SUPERIEUR_500,
    ):
        bdese, _ = BDESE_300.objects.get_or_create(entreprise=entreprise, annee=annee)
    else:
        bdese, _ = BDESE_50_300.objects.get_or_create(
            entreprise=entreprise, annee=annee
        )
    return bdese


@login_required
def bdese_configuration(request, siren, annee):
    entreprise = Entreprise.objects.get(siren=siren)
    if request.user not in entreprise.users.all():
        raise PermissionDenied

    bdese = _get_or_create_bdese(entreprise, annee)

    initial = None
    if not bdese.categories_professionnelles and not request.POST:
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
                break

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

    return render(
        request,
        _bdese_step_template_path(bdese, 0),
        _bdese_step_context(form, siren, annee, bdese, 0),
    )
