from dataclasses import dataclass, field

import requests
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import HttpResponse, render
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from weasyprint import HTML

from entreprises.models import Entreprise
from public.forms import EligibiliteForm
from .forms import bdese_form_factory
from .models import BDESE, categories_default


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
            elif entreprise.effectif == "grand":
                bdese_type = cls.TYPE_INFERIEUR_500
            else:
                bdese_type = cls.TYPE_SUPERIEUR_500
            if BDESE.objects.filter(entreprise__siren=entreprise.siren, annee=2022):
                status = cls.STATUS_EN_COURS
                status_detail = "Vous êtes soumis à cette réglementation. Vous avez démarré le remplissage de votre BDESE sur la plateforme"
                primary_action = ReglementationAction(
                    reverse_lazy("bdese", args=[entreprise.siren]),
                    "Reprendre l'actualisation de ma BDESE",
                )
            else:
                status = cls.STATUS_A_ACTUALISER
                status_detail = "Vous êtes soumis à cette réglementation. Nous allons vous aider à la remplir."
                primary_action = ReglementationAction(
                    reverse_lazy("bdese", args=[entreprise.siren]),
                    "Actualiser ma BDESE",
                )
            secondary_actions = [
                ReglementationAction(
                    reverse_lazy("result")
                    + f"?raison_sociale={ entreprise.raison_sociale }&bdese={ bdese_type }",
                    "Télécharger le pdf",
                ),
            ]
            return cls(
                status,
                status_detail,
                primary_action=primary_action,
                secondary_actions=secondary_actions,
                bdese_type=bdese_type,
            )


@dataclass
class IndexEgaproReglementation(Reglementation):
    title = "Index de l'égalité professionnelle"
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
        elif is_index_egapro_updated(entreprise.siren):
            status = cls.STATUS_ACTUALISE
            status_detail = "Vous êtes soumis à cette réglementation. Vous avez rempli vos obligations d'après les données disponibles sur Index Egapro."
        else:
            status = cls.STATUS_A_ACTUALISER
            status_detail = "Vous êtes soumis à cette réglementation. Vous n'avez pas encore déclaré votre index sur Index Egapro."
        return cls(status, status_detail)


def is_index_egapro_updated(siren):
    url = f"https://index-egapro.travail.gouv.fr/api/search?q={siren}"
    response = requests.get(url)
    if response.status_code == 200:
        if index_egapro_data := response.json()["data"]:
            if "2021" in index_egapro_data[0]["notes"]:
                return True
    return False


def reglementations(request):
    if request.user and request.user.is_authenticated:
        return _reglementations_connecte(request)

    form = EligibiliteForm(request.GET)
    if "siren" in form.data:
        entreprise = Entreprise.objects.filter(siren=form.data["siren"])
        if entreprise:
            form = EligibiliteForm(request.GET, instance=entreprise[0])
    if form and form.is_valid():
        siren = form.cleaned_data["siren"]
        request.session["siren"] = siren
        entreprise = form.save()
    else:
        return render(
            request,
            "reglementations/reglementations.html",
            {
                "entreprises": [
                    {
                        "entreprise": None,
                        "reglementations": [
                            BDESEReglementation(),
                            IndexEgaproReglementation(),
                        ],
                    },
                ]
            },
        )

    return render(
        request,
        "reglementations/reglementations.html",
        {
            "entreprises": [
                {
                    "entreprise": entreprise,
                    "reglementations": [
                        BDESEReglementation.calculate(entreprise),
                        IndexEgaproReglementation.calculate(entreprise),
                    ],
                },
            ]
        },
    )


def _reglementations_connecte(request):
    entreprises = request.user.entreprise_set.all()
    return render(
        request,
        "reglementations/reglementations.html",
        {
            "entreprises": [
                {
                    "entreprise": entreprise,
                    "reglementations": [
                        BDESEReglementation.calculate(entreprise),
                        IndexEgaproReglementation.calculate(entreprise),
                    ],
                }
                for entreprise in entreprises
            ]
        },
    )


def result(request):
    bdese_type = int(request.GET["bdese"])
    if bdese_type == BDESEReglementation.TYPE_AVEC_ACCORD:
        bdese = "REGLEMENTATION AVEC ACCORD"
    elif bdese_type == BDESEReglementation.TYPE_INFERIEUR_300:
        bdese = "REGLEMENTATION MOINS DE 300 SALARIES"
    elif bdese_type == BDESEReglementation.TYPE_INFERIEUR_500:
        bdese = "REGLEMENTATION PLUS DE 300 SALARIES"
    elif bdese_type == BDESEReglementation.TYPE_SUPERIEUR_500:
        bdese = "REGLEMENTATION PLUS DE 500 SALARIES"
    context = {
        "raison_sociale": request.GET["raison_sociale"],
        "bdese": bdese,
    }
    pdf_html = render_to_string("reglementations/result_pdf.html", context)
    pdf_file = HTML(string=pdf_html).write_pdf()

    response = HttpResponse(pdf_file, content_type="application/pdf")
    response["Content-Disposition"] = 'filename="mypdf.pdf"'
    return response


def get_bdese_data_from_index_egapro(siren, year):
    url = f"https://index-egapro.travail.gouv.fr/api/declarations/{siren}"
    response = requests.get(url)
    if response.status_code == 200:
        bdese_data_from_index_egapro = {}
        for declaration in response.json():
            if declaration["year"] == year:
                index_egapro_data = declaration["data"]
                indicateur_hautes_remunerations = index_egapro_data["indicateurs"][
                    "hautes_rémunérations"
                ]
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
def bdese(request, siren):
    entreprise = Entreprise.objects.get(siren=siren)
    if request.user not in entreprise.users.all():
        raise PermissionDenied
    bdese, created = BDESE.objects.get_or_create(entreprise=entreprise)
    categories_professionnelles = categories_default()
    if request.method == "POST":
        form = bdese_form_factory(
            categories_professionnelles, data=request.POST, instance=bdese
        )
        if form.is_valid():
            bdese = form.save()
        else:
            print(form.errors)
    else:
        fetched_data = get_bdese_data_from_index_egapro(siren, 2021)
        form = bdese_form_factory(
            categories_professionnelles, fetched_data=fetched_data, instance=bdese
        )
    return render(request, "reglementations/bdese.html", {"form": form, "siren": siren})
