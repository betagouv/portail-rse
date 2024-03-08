from datetime import date
from datetime import datetime
from datetime import timezone

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render

import api.recherche_entreprises
from api.exceptions import APIError
from entreprises.forms import EntrepriseAttachForm
from entreprises.forms import EntrepriseDetachForm
from entreprises.forms import EntrepriseQualificationForm
from entreprises.models import ActualisationCaracteristiquesAnnuelles
from entreprises.models import CaracteristiquesAnnuelles
from entreprises.models import Entreprise
from habilitations.models import attach_user_to_entreprise
from habilitations.models import detach_user_from_entreprise
from habilitations.models import is_user_attached_to_entreprise


def get_current_entreprise(request):
    if siren := request.session.get("entreprise"):
        try:
            entreprise = Entreprise.objects.get(siren=siren)
        except ObjectDoesNotExist:
            entreprise = None
            del request.session["entreprise"]
    elif request.user.is_authenticated and (
        entreprises := request.user.entreprise_set.all()
    ):
        entreprise = entreprises[0]
    else:
        entreprise = None
    return entreprise


@login_required()
def index(request):
    if request.POST:
        if request.POST["action"] == "attach":
            return attach(request)
        else:
            form = EntrepriseDetachForm(request.POST)
            if form.is_valid():
                siren = form.cleaned_data["siren"]
                try:
                    entreprise = Entreprise.objects.get(siren=siren)
                    detach_user_from_entreprise(request.user, entreprise)
                    entreprise_in_session = request.session.get("entreprise")
                    if entreprise_in_session == entreprise.siren:
                        del request.session["entreprise"]
                    messages.success(
                        request,
                        f"Votre compte n'êtes plus rattaché à l'entreprise {entreprise.denomination}",
                    )
                except ObjectDoesNotExist:
                    messages.error(request, "Impossible de quitter cette entreprise")
            return redirect("entreprises:entreprises")

    return render(request, "entreprises/index.html", {"form": EntrepriseAttachForm()})


class _InvalidRequest(Exception):
    pass


def search_and_create_entreprise(siren):
    try:
        infos_entreprise = api.recherche_entreprises.recherche(siren)
    except APIError as exception:
        raise exception
    return Entreprise.objects.create(
        siren=infos_entreprise["siren"],
        denomination=infos_entreprise["denomination"],
        categorie_juridique_sirene=infos_entreprise["categorie_juridique_sirene"],
        code_pays_etranger_sirene=infos_entreprise["code_pays_etranger_sirene"],
    )


def attach(request):
    form = EntrepriseAttachForm(request.POST)
    try:
        if form.is_valid():
            siren = form.cleaned_data["siren"]
            if entreprises := Entreprise.objects.filter(siren=siren):
                entreprise = entreprises[0]
            else:
                entreprise = search_and_create_entreprise(siren)
            if is_user_attached_to_entreprise(request.user, entreprise):
                raise _InvalidRequest(
                    "Impossible d'ajouter cette entreprise. Vous y êtes déjà rattaché·e."
                )
            else:
                attach_user_to_entreprise(
                    request.user,
                    entreprise,
                    form.cleaned_data["fonctions"],
                )
        else:
            raise _InvalidRequest(
                "Impossible de créer l'entreprise car les données sont incorrectes."
            )
    except (_InvalidRequest, APIError) as exception:
        messages.error(
            request,
            exception,
        )
        return render(request, "entreprises/index.html", {"form": form})

    messages.success(request, "L'entreprise a été ajoutée.")
    return redirect("entreprises:entreprises")


@login_required
def qualification(request, siren):
    entreprise = get_object_or_404(Entreprise, siren=siren)
    if not is_user_attached_to_entreprise(request.user, entreprise):
        raise PermissionDenied

    if request.POST:
        form = EntrepriseQualificationForm(data=request.POST)
        if form.is_valid():
            date_cloture_dernier_exercice = form.cleaned_data["date_cloture_exercice"]
            entreprise.date_cloture_exercice = date_cloture_dernier_exercice
            entreprise.est_cotee = form.cleaned_data["est_cotee"]
            entreprise.est_interet_public = form.cleaned_data["est_interet_public"]
            entreprise.appartient_groupe = form.cleaned_data["appartient_groupe"]
            entreprise.est_societe_mere = form.cleaned_data["est_societe_mere"]
            entreprise.societe_mere_en_france = form.cleaned_data[
                "societe_mere_en_france"
            ]
            entreprise.comptes_consolides = form.cleaned_data["comptes_consolides"]
            entreprise.date_derniere_qualification = datetime.now(tz=timezone.utc)
            entreprise.save()
            actualisation = ActualisationCaracteristiquesAnnuelles(
                date_cloture_dernier_exercice,
                form.cleaned_data["effectif"],
                form.cleaned_data["effectif_permanent"],
                form.cleaned_data["effectif_outre_mer"],
                form.cleaned_data["effectif_groupe"],
                form.cleaned_data["effectif_groupe_france"],
                form.cleaned_data["effectif_groupe_permanent"],
                form.cleaned_data["tranche_chiffre_affaires"],
                form.cleaned_data["tranche_bilan"],
                form.cleaned_data["tranche_chiffre_affaires_consolide"],
                form.cleaned_data["tranche_bilan_consolide"],
                form.cleaned_data["bdese_accord"],
                form.cleaned_data["systeme_management_energie"],
            )
            caracteristiques = entreprise.actualise_caracteristiques(actualisation)
            caracteristiques.save()
            CaracteristiquesAnnuelles.objects.filter(
                entreprise=entreprise, annee__gt=date_cloture_dernier_exercice.year
            ).delete()
            messages.success(
                request, "Les informations de l'entreprise ont été mises à jour."
            )
            return redirect("reglementations:tableau_de_bord", siren=siren)
        else:
            messages.error(
                request,
                "Les informations de l'entreprise n'ont pas été mises à jour car le formulaire contient des erreurs.",
            )
    else:
        date_cloture_exercice_par_defaut = date(date.today().year - 1, 12, 31)
        if (
            caracs := entreprise.dernieres_caracteristiques_qualifiantes
            or entreprise.dernieres_caracteristiques
        ):
            infos_entreprise = {
                "date_cloture_exercice": caracs.date_cloture_exercice.isoformat()
                if caracs.date_cloture_exercice
                else date_cloture_exercice_par_defaut.isoformat(),
                "effectif": caracs.effectif,
                "effectif_permanent": caracs.effectif_permanent,
                "effectif_outre_mer": caracs.effectif_outre_mer,
                "tranche_chiffre_affaires": caracs.tranche_chiffre_affaires,
                "tranche_bilan": caracs.tranche_bilan,
                "est_cotee": entreprise.est_cotee,
                "est_interet_public": entreprise.est_interet_public,
                "appartient_groupe": entreprise.appartient_groupe,
                "effectif_groupe": caracs.effectif_groupe,
                "effectif_groupe_france": caracs.effectif_groupe_france,
                "effectif_groupe_permanent": caracs.effectif_groupe_permanent,
                "est_societe_mere": entreprise.est_societe_mere,
                "societe_mere_en_france": entreprise.societe_mere_en_france,
                "comptes_consolides": entreprise.comptes_consolides,
                "tranche_chiffre_affaires_consolide": caracs.tranche_chiffre_affaires_consolide,
                "tranche_bilan_consolide": caracs.tranche_bilan_consolide,
                "bdese_accord": caracs.bdese_accord,
                "systeme_management_energie": caracs.systeme_management_energie,
            }
        else:
            try:
                infos_entreprise = api.recherche_entreprises.recherche(entreprise.siren)
            except APIError:
                infos_entreprise = {}
            infos_entreprise[
                "date_cloture_exercice"
            ] = date_cloture_exercice_par_defaut.isoformat()
        form = EntrepriseQualificationForm(initial=infos_entreprise)

    return render(
        request,
        "entreprises/qualification.html",
        context={"entreprise": entreprise, "form": form},
    )


def search_entreprise(request, siren):
    try:
        return JsonResponse(api.recherche_entreprises.recherche(siren))
    except APIError as exception:
        return JsonResponse(
            {"error": str(exception)},
            status=400,
        )
