from datetime import date

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import BadRequest
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render

import api.infos_entreprise
from api.exceptions import APIError
from entreprises.forms import EntrepriseAttachForm
from entreprises.forms import EntrepriseDetachForm
from entreprises.forms import EntrepriseQualificationForm
from entreprises.forms import PreremplissageSirenForm
from entreprises.models import Entreprise
from habilitations.models import Habilitation
from habilitations.models import HabilitationError
from users.forms import message_erreur_proprietaires


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
                    Habilitation.retirer(entreprise, request.user)
                    entreprise_in_session = request.session.get("entreprise")
                    if entreprise_in_session == entreprise.siren:
                        del request.session["entreprise"]
                    messages.success(
                        request,
                        f"Votre compte n'est plus rattaché à l'entreprise {entreprise.denomination}",
                    )
                    return redirect("entreprises:entreprises")
                except ObjectDoesNotExist:
                    messages.error(request, "Impossible de quitter cette entreprise")
                except HabilitationError as h_err:
                    messages.error(request, str(h_err))
            en_provenance_du_tableau_de_bord = request.META.get(
                "HTTP_REFERER"
            ) and "tableau-de-bord" in request.META.get("HTTP_REFERER")
            return (
                redirect("reglementations:tableau_de_bord")
                if en_provenance_du_tableau_de_bord
                else redirect("entreprises:entreprises")
            )

    return render(request, "entreprises/index.html", {"form": EntrepriseAttachForm()})


class _InvalidRequest(Exception):
    pass


def attach(request):
    form = EntrepriseAttachForm(request.POST)
    try:
        if form.is_valid():
            siren = form.cleaned_data["siren"]
            if entreprises := Entreprise.objects.filter(siren=siren):
                entreprise = entreprises[0]
            else:
                entreprise = Entreprise.search_and_create_entreprise(siren)
            if habilitations := Habilitation.objects.filter(
                entreprise=entreprise
            ).all():
                for habilitation in habilitations:
                    if habilitation.user == request.user:
                        raise _InvalidRequest(
                            "Impossible d'ajouter cette entreprise. Vous y êtes déjà rattaché·e."
                        )
                cause_erreur = message_erreur_proprietaires(
                    [habilitation.user for habilitation in habilitations]
                )
            if habilitations := Habilitation.objects.filter(
                entreprise=entreprise
            ).all():
                cause_erreur = message_erreur_proprietaires(
                    [habilitation.user for habilitation in habilitations]
                )
                raise _InvalidRequest(
                    f"Impossible d'ajouter cette entreprise. {cause_erreur}"
                )

            else:
                Habilitation.ajouter(
                    entreprise,
                    request.user,
                    fonctions=form.cleaned_data["fonctions"],
                )
        else:
            raise _InvalidRequest(
                "Impossible d'ajouter cette entreprise car les données sont incorrectes."
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
    if not Habilitation.existe(entreprise, request.user):
        raise PermissionDenied

    if request.POST:
        form = EntrepriseQualificationForm(data=request.POST, entreprise=entreprise)
        if form.is_valid():
            form.save()

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
                "date_cloture_exercice": caracs.date_cloture_exercice
                or date_cloture_exercice_par_defaut,
                "effectif": caracs.effectif,
                "effectif_securite_sociale": caracs.effectif_securite_sociale,
                "effectif_outre_mer": caracs.effectif_outre_mer,
                "tranche_chiffre_affaires": caracs.tranche_chiffre_affaires,
                "tranche_bilan": caracs.tranche_bilan,
                "est_cotee": entreprise.est_cotee,
                "est_interet_public": entreprise.est_interet_public,
                "appartient_groupe": entreprise.appartient_groupe,
                "effectif_groupe": caracs.effectif_groupe,
                "effectif_groupe_france": caracs.effectif_groupe_france,
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
                infos_entreprise = api.infos_entreprise.infos_entreprise(
                    entreprise.siren, donnees_financieres=True
                )
                if infos_entreprise["tranche_chiffre_affaires_consolide"]:
                    infos_entreprise["appartient_groupe"] = True
                    infos_entreprise["comptes_consolides"] = True
            except APIError:
                infos_entreprise = {}
            if "date_cloture_exercice" not in infos_entreprise:
                infos_entreprise["date_cloture_exercice"] = (
                    date_cloture_exercice_par_defaut
                )
        form = EntrepriseQualificationForm(
            initial=infos_entreprise, entreprise=entreprise
        )

    return render(
        request,
        "entreprises/qualification.html",
        context={"entreprise": entreprise, "form": form},
    )


def recherche_entreprise(request):
    nombre_resultats = 0
    entreprises = []
    erreur_recherche_entreprise = None
    try:
        recherche = request.GET["recherche"]
    except KeyError:
        raise BadRequest()
    if recherche == settings.SIREN_ENTREPRISE_TEST:
        nombre_resultats = 1
        entreprises = [
            {
                "siren": settings.SIREN_ENTREPRISE_TEST,
                "denomination": "ENTREPRISE TEST",
                "activite": "Cultures non permanentes",
            }
        ]
    elif len(recherche) >= 3:
        try:
            resultats = api.infos_entreprise.recherche_par_nom_ou_siren(recherche)
            nombre_resultats = resultats["nombre_resultats"]
            entreprises = resultats["entreprises"]
        except APIError as e:
            erreur_recherche_entreprise = str(e)
    return render(
        request,
        "fragments/resultats_recherche_entreprise.html",
        context={
            "nombre_resultats": nombre_resultats,
            "entreprises": entreprises,
            "erreur_recherche_entreprise": erreur_recherche_entreprise,
            "recherche": recherche,
            "htmx_fragment_view_name": request.GET.get("htmx_fragment_view_name"),
        },
    )


def preremplissage_siren(request):
    form = PreremplissageSirenForm(request.GET)
    return render(
        request,
        "fragments/siren_field.html",
        context={"form": form},
    )
