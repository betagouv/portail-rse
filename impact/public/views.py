from dataclasses import dataclass, field

import requests
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.shortcuts import HttpResponse, render
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from weasyprint import HTML

from .forms import bdese_form_factory, EligibiliteForm, SirenForm
from .models import BDESE, Entreprise, categories_default


def index(request):
    return render(request, "public/index.html", {"form": SirenForm()})


def siren(request):
    form = SirenForm(request.GET)
    errors = []
    if form.is_valid():
        siren = form.cleaned_data["siren"]

        url = f"https://entreprise.api.gouv.fr/v3/insee/sirene/unites_legales/{siren}"
        headers = {"Authorization": f"Bearer {settings.API_ENTREPRISE_TOKEN}"}
        params = {
            "context": "Test de l'API",
            "object": "Test de l'API",
            "recipient": "10000001700010",
        }

        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()["data"]
            raison_sociale = data["personne_morale_attributs"]["raison_sociale"]
            effectif = data["tranche_effectif_salarie"]["a"]
            if effectif < 50:
                taille = "petit"
            elif effectif < 300:
                taille = "moyen"
            elif effectif < 500:
                taille = "grand"
            else:
                taille = "sup500"
            form = EligibiliteForm(
                initial={
                    "siren": siren,
                    "effectif": taille,
                    "raison_sociale": raison_sociale,
                }
            )
            return render(
                request,
                "public/siren.html",
                {
                    "raison_sociale": raison_sociale,
                    "form": form,
                },
            )
        else:
            errors = response.json()["errors"]
    else:
        errors = form.errors

    return render(request, "public/index.html", {"form": form, "errors": errors})


@dataclass
class ReglementationAction:
    url: str
    title: str


@dataclass
class Reglementation:
    STATUS_ACTUALISE = "actualisé"
    STATUS_A_ACTUALISER = "à actualiser"
    STATUS_EN_COURS = "en cours"
    STATUS_NON_SOUMIS = "non soumis"

    status: str
    status_detail: str


@dataclass
class _Entreprise:
    effectif: str
    accord: bool
    raison_sociale: str
    siren: str


@dataclass
class BDESEReglementation(Reglementation):
    TYPE_AVEC_ACCORD = 1
    TYPE_INFERIEUR_300 = 2
    TYPE_INFERIEUR_500 = 3
    TYPE_SUPERIEUR_500 = 4

    primary_action: ReglementationAction | None = None
    secondary_actions: list[ReglementationAction] = field(default_factory=list)
    bdese_type: int | None = None

    @classmethod
    def calculate(cls, entreprise: _Entreprise) -> "BDESEReglementation":
        if entreprise.effectif == "petit":
            status = cls.STATUS_NON_SOUMIS
            status_detail = "Vous n'êtes pas soumis à cette réglementation"
            return cls(status, status_detail)
        elif entreprise.accord:
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
                    reverse_lazy("bdese", args=[entreprise.siren]), "Reprendre l'actualisation de ma BDESE"
                )
            else:
                status = cls.STATUS_A_ACTUALISER
                status_detail = "Vous êtes soumis à cette réglementation. Nous allons vous aider à la remplir."
                primary_action = ReglementationAction(
                    reverse_lazy("bdese", args=[entreprise.siren]), "Actualiser ma BDESE"
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
    @classmethod
    def calculate(cls, entreprise: _Entreprise) -> "IndexEgaproReglementations":
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
    if form.is_valid():
        siren = form.cleaned_data["siren"]
        request.session["siren"] = siren
        entreprise, _ = Entreprise.objects.get_or_create(siren=siren)
        entreprise.effectif = form.cleaned_data["effectif"]
        entreprise.accord = form.cleaned_data["accord"]
        entreprise.raison_sociale = form.cleaned_data["raison_sociale"]
    return render(
        request,
        "public/reglementations.html",
        {
            "entreprises": [
                {
                    "entreprise": entreprise,
                    "bdese": BDESEReglementation.calculate(entreprise),
                    "index_egapro": IndexEgaproReglementation.calculate(entreprise),
                },
            ]
        },
    )


def _reglementations_connecte(request):
    entreprises = request.user.entreprise_set.all()
    return render(
        request,
        "public/reglementations.html",
        {
            "entreprises": [
                {
                    "entreprise": entreprise,
                    "bdese": BDESEReglementation.calculate(entreprise),
                    "index_egapro": IndexEgaproReglementation.calculate(entreprise),
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
    pdf_html = render_to_string("public/result_pdf.html", context)
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
    return render(request, "public/bdese.html", {"form": form, "siren": siren})
