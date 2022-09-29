import requests
from django.conf import settings
from django.shortcuts import HttpResponse, render
from django.template.loader import render_to_string
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
            Entreprise.objects.get_or_create(siren=siren)
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


BDESE_ELIGIBILITE = {
    "NON_ELIGIBLE": 0,
    "ELIGIBLE_AVEC_ACCORD": 1,
    "ELIGIBLE_INFERIEUR_300": 2,
    "ELIGIBLE_INFERIEUR_500": 3,
    "ELIGIBLE_SUPERIEUR_500": 4,
}


def eligibilite(request):
    form = EligibiliteForm(request.GET)
    if form.is_valid():
        accord = form.cleaned_data["accord"]
        effectif = form.cleaned_data["effectif"]
        raison_sociale = form.cleaned_data["raison_sociale"]
        siren = form.cleaned_data["siren"]
        if effectif == "petit":
            bdese_result = BDESE_ELIGIBILITE["NON_ELIGIBLE"]
        elif accord:
            bdese_result = BDESE_ELIGIBILITE["ELIGIBLE_AVEC_ACCORD"]
        elif effectif == "moyen":
            bdese_result = BDESE_ELIGIBILITE["ELIGIBLE_INFERIEUR_300"]
        elif effectif == "grand":
            bdese_result = BDESE_ELIGIBILITE["ELIGIBLE_INFERIEUR_500"]
        else:
            bdese_result = BDESE_ELIGIBILITE["ELIGIBLE_SUPERIEUR_500"]

    return render(
        request,
        "public/result.html",
        {
            "BDESE_ELIGIBILITE": BDESE_ELIGIBILITE,
            "bdese_result": bdese_result,
            "raison_sociale": raison_sociale,
            "siren": siren,
        },
    )


def result(request):
    context = {
        "raison_sociale": request.GET["raison_sociale"],
        "bdese": int(request.GET["bdese"]),
        "BDESE_ELIGIBILITE": BDESE_ELIGIBILITE,
    }
    pdf_html = render_to_string("public/result_pdf.html", context)
    pdf_file = HTML(string=pdf_html).write_pdf()

    response = HttpResponse(pdf_file, content_type="application/pdf")
    response["Content-Disposition"] = 'filename="mypdf.pdf"'
    return response


def bdese(request, siren):
    entreprise = Entreprise.objects.get(siren=siren)
    bdese, created = BDESE.objects.get_or_create(entreprise=entreprise)
    categories = categories_default()
    if request.method == "POST":
        form = bdese_form_factory(categories, request.POST, instance=bdese)
        if form.is_valid():
            bdese = form.save()
        else:
            print(form.errors)
    else:
        form = bdese_form_factory(categories, instance=bdese)
    return render(request, "public/bdese.html", {"form": form, "siren": siren})
