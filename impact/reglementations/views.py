from dataclasses import dataclass, field

import requests
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import HttpResponse, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from weasyprint import CSS, HTML
from weasyprint.text.fonts import FontConfiguration

from entreprises.models import Entreprise
from public.forms import EligibiliteForm
from .forms import bdese_form_factory
from .models import BDESE_300, BDESE_50_300, categories_default


@dataclass
class ReglementationAction:
    url: str
    title: str
    external: bool = False


@dataclass
class Reglementation:
    STATUS_ACTUALISE = "actualisé"
    STATUS_A_ACTUALISER = "à actualiser"
    STATUS_EN_COURS = "en cours"
    STATUS_NON_SOUMIS = "non soumis"

    status: str | None = None
    status_detail: str | None = None


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

    primary_action: ReglementationAction | None = None
    secondary_actions: list[ReglementationAction] = field(default_factory=list)
    bdese_type: int | None = None

    @classmethod
    def calculate(cls, entreprise: Entreprise) -> "BDESEReglementation":
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
                entreprise__siren=entreprise.siren, annee=2022
            )
            if bdese:
                bdese = bdese[0]
                if bdese.is_complete:
                    status = cls.STATUS_ACTUALISE
                    status_detail = "Vous êtes soumis à cette réglementation. Vous avez actualisé votre BDESE sur la plateforme."
                    primary_action = ReglementationAction(
                        reverse_lazy("bdese_result", args=[entreprise.siren]),
                        "Télécharger le pdf",
                    )
                    secondary_actions = [
                        ReglementationAction(
                            reverse_lazy("bdese", args=[entreprise.siren, 1]),
                            "Modifier ma BDESE",
                        )
                    ]
                else:
                    status = cls.STATUS_EN_COURS
                    status_detail = "Vous êtes soumis à cette réglementation. Vous avez démarré le remplissage de votre BDESE sur la plateforme."
                    primary_action = ReglementationAction(
                        reverse_lazy("bdese", args=[entreprise.siren, 1]),
                        "Reprendre l'actualisation de ma BDESE",
                    )
                    secondary_actions = [
                        ReglementationAction(
                            reverse_lazy("bdese_result", args=[entreprise.siren]),
                            "Télécharger le pdf (brouillon)",
                        ),
                    ]
            else:
                status = cls.STATUS_A_ACTUALISER
                status_detail = "Vous êtes soumis à cette réglementation. Nous allons vous aider à la remplir."
                primary_action = ReglementationAction(
                    reverse_lazy("bdese", args=[entreprise.siren, 1]),
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
    primary_action = ReglementationAction(
        "https://index-egapro.travail.gouv.fr/",
        "Calculer et déclarer mon index sur Index Egapro",
        external=True,
    )

    @classmethod
    def calculate(cls, entreprise: Entreprise) -> "IndexEgaproReglementations":
        if entreprise.effectif == "petit":
            status = cls.STATUS_NON_SOUMIS
            status_detail = "Vous n'êtes pas soumis à cette réglementation"
        elif is_index_egapro_updated(entreprise):
            status = cls.STATUS_ACTUALISE
            status_detail = "Vous êtes soumis à cette réglementation. Vous avez rempli vos obligations d'après les données disponibles sur Index Egapro."
        else:
            status = cls.STATUS_A_ACTUALISER
            status_detail = "Vous êtes soumis à cette réglementation. Vous n'avez pas encore déclaré votre index sur Index Egapro."
        return cls(status, status_detail)


def is_index_egapro_updated(entreprise: Entreprise) -> bool:
    url = f"https://index-egapro.travail.gouv.fr/api/search?q={entreprise.siren}"
    response = requests.get(url)
    if response.status_code == 200:
        if index_egapro_data := response.json()["data"]:
            if "2021" in index_egapro_data[0]["notes"]:
                return True
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
                        BDESEReglementation.calculate(entreprise)
                        if entreprise
                        else BDESEReglementation(),
                        IndexEgaproReglementation.calculate(entreprise)
                        if entreprise
                        else IndexEgaproReglementation(),
                    ],
                }
                for entreprise in entreprises
            ]
        },
    )


@login_required
def bdese_result(request, siren):
    entreprise = Entreprise.objects.get(siren=siren)
    if request.user not in entreprise.users.all():
        raise PermissionDenied
    bdese = _get_or_create_bdese(entreprise)
    categories_professionnelles = categories_default()
    bdese_form = bdese_form_factory(1, categories_professionnelles, bdese)
    context = {
        "entreprise": entreprise,
        "bdese_form": bdese_form,
    }
    pdf_html = render_to_string("reglementations/bdese_result_pdf.html", context)
    font_config = FontConfiguration()
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


def get_bdese_data_from_index_egapro(entreprise: Entreprise, year: int) -> dict:
    bdese_data_from_index_egapro = {}
    url = f"https://index-egapro.travail.gouv.fr/api/declarations/{entreprise.siren}"
    response = requests.get(url)
    if response.status_code == 200:
        for declaration in response.json():
            if declaration["year"] == year:
                index_egapro_data = declaration["data"]
                if indicateur_hautes_remunerations := index_egapro_data.get(
                    "indicateurs", {}
                ).get("hautes_rémunérations"):
                    bdese_data_from_index_egapro = {
                        "nombre_femmes_plus_hautes_remunerations": int(
                            indicateur_hautes_remunerations["résultat"]
                        )
                        if indicateur_hautes_remunerations["population_favorable"]
                        == "hommes"
                        else 10 - int(indicateur_hautes_remunerations["résultat"])
                    }
                break
    return bdese_data_from_index_egapro


@login_required
def bdese(request, siren, step):
    entreprise = Entreprise.objects.get(siren=siren)
    if request.user not in entreprise.users.all():
        raise PermissionDenied
    bdese = _get_or_create_bdese(entreprise)
    categories_professionnelles = categories_default()
    if request.method == "POST":
        if "mark_incomplete" in request.POST:
            bdese.mark_step_as_incomplete(step)
            bdese.save()
            return redirect("bdese", siren=siren, step=step)
        else:
            form = bdese_form_factory(
                step,
                categories_professionnelles,
                bdese,
                data=request.POST,
            )
            if form.is_valid():
                bdese = form.save()
                messages.success(request, "Étape enregistrée")
                if "save_complete" in request.POST:
                    bdese.mark_step_as_complete(step)
                    bdese.save()
                    return redirect("bdese", siren=siren, step=step)
            else:
                messages.error(
                    request,
                    "L'étape n'a pas été enregistrée car le formulaire contient des erreurs",
                )
    else:
        fetched_data = get_bdese_data_from_index_egapro(entreprise, 2021)
        form = bdese_form_factory(
            step, categories_professionnelles, bdese, fetched_data=fetched_data
        )
    if bdese.__class__ == BDESE_300:
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
        template_path = f"reglementations/bdese_300/{templates[step]}"
        steps = {
            step: {
                "name": bdese.STEPS[step],
                "is_complete": bdese.step_is_complete(step),
            }
            for step in bdese.STEPS
        }
        step_is_complete = steps[step]["is_complete"]
    else:
        template_path = "reglementations/bdese_50_300.html"
        steps = {}
        step_is_complete = False
    return render(
        request,
        template_path,
        {
            "form": form,
            "siren": siren,
            "step_is_complete": step_is_complete,
            "steps": steps,
        },
    )


def _get_or_create_bdese(entreprise: Entreprise) -> BDESE_300 | BDESE_50_300:
    reglementation = BDESEReglementation.calculate(entreprise)
    if reglementation.bdese_type in (
        BDESEReglementation.TYPE_INFERIEUR_500,
        BDESEReglementation.TYPE_SUPERIEUR_500,
    ):
        bdese, _ = BDESE_300.objects.get_or_create(entreprise=entreprise)
    else:
        bdese, _ = BDESE_50_300.objects.get_or_create(entreprise=entreprise)
    return bdese
