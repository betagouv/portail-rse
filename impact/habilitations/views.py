from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMessage
from django.http.response import HttpResponseBadRequest
from django.http.response import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .enums import UserRole
from .forms import InvitationForm
from .models import Habilitation
from .models import HabilitationError
from entreprises.models import Entreprise
from habilitations.decorators import role
from invitations.models import Invitation
from users.models import User
from utils.htmx import HttpResponseRedirectSeeOther
from utils.tokens import make_token


@login_required()
@require_http_methods(["POST"])
@role(UserRole.PROPRIETAIRE)
def invitation(request, siren):
    # le SIREN dans l'URL doit correspondre au SIREN de l'entreprise courante en session
    siren_session = request.session.get("entreprise")
    if siren != siren_session:
        return HttpResponseForbidden(
            "Le SIREN demandé ne correspond pas à l'entreprise courante."
        )

    entreprise = get_object_or_404(Entreprise, siren=siren)
    request.session["entreprise"] = siren
    form = InvitationForm(request.POST)
    if form.is_valid():
        email = form.cleaned_data["email"]
        role = form.cleaned_data["role"]
        try:
            utilisateur = User.objects.get(email=email)
            if Habilitation.objects.filter(entreprise=entreprise, user=utilisateur):
                messages.error(
                    request,
                    "L'invitation a échoué car cette personne est déjà membre de l'entreprise.",
                )
            else:
                _ajoute_membre(request, entreprise, utilisateur, role)
        except ObjectDoesNotExist:
            _cree_invitation(request, entreprise, email, role)
        return redirect(
            reverse("reglementations:tableau_de_bord", args=[entreprise.siren])
        )
    else:
        request.session["invitation_form"] = request.POST
        messages.error(
            request,
            "L'invitation a échoué car le formulaire contient des erreurs.",
        )
        return redirect(
            reverse("reglementations:tableau_de_bord", args=[entreprise.siren])
        )


def contributeurs_context(request, entreprise):
    invitation_form = request.session.pop("invitation_form", None)
    context = {
        "form": (
            InvitationForm(invitation_form) if invitation_form else InvitationForm()
        ),
        "entreprise": entreprise,
        "habilitation": Habilitation.pour(entreprise, request.user),
        "invitations": Invitation.objects.filter(
            entreprise=entreprise, date_acceptation__isnull=True
        ),
        "habilitations": Habilitation.objects.filter(
            entreprise=entreprise, user__is_email_confirmed=True
        ).order_by("user__nom"),
    }
    return context


def _ajoute_membre(request, entreprise, utilisateur, role):
    invitation = Invitation.objects.create(
        entreprise=entreprise,
        email=utilisateur.email,
        role=role,
        inviteur=request.user,
    )
    invitation.accepter(utilisateur)
    _envoie_email_d_ajout(request, entreprise, utilisateur)
    messages.success(
        request,
        "L'utilisateur a été ajouté.",
    )


def _envoie_email_d_ajout(request, entreprise, utilisateur):
    email = EmailMessage(
        to=[utilisateur.email],
        from_email=settings.DEFAULT_FROM_EMAIL,
    )
    email.template_id = settings.BREVO_AJOUT_MEMBRE_TEMPLATE
    path = f"""{reverse("entreprises:entreprises")}"""
    url = f"{request.build_absolute_uri(path)}"
    inviteur = request.user
    email.merge_global_data = {
        "denomination_entreprise": entreprise.denomination,
        "membres_url": url,
        "inviteur": f"{inviteur.prenom} {inviteur.nom}",
    }
    email.send()


def _cree_invitation(request, entreprise, email, role):
    invitation = Invitation.objects.create(
        entreprise=entreprise,
        email=email,
        role=role,
        inviteur=request.user,
    )
    _envoie_email_d_invitation(request, invitation)
    messages.success(
        request,
        "L'invitation a été envoyée.",
    )


def _envoie_email_d_invitation(request, invitation):
    email = EmailMessage(
        to=[invitation.email],
        from_email=settings.DEFAULT_FROM_EMAIL,
    )
    email.template_id = settings.BREVO_INVITATION_TEMPLATE
    code = make_token(invitation, "invitation")
    path = reverse(
        "users:invitation",
        args=[invitation.id, code],
    )
    url = f"{request.build_absolute_uri(path)}"
    email.merge_global_data = {
        "denomination_entreprise": invitation.entreprise.denomination,
        "invitation_url": url,
        "inviteur": f"{invitation.inviteur.prenom} {invitation.inviteur.nom}",
        "role": invitation.get_role_display(),
    }
    email.send()


# Gestion des droits par les propriétaires


@login_required
@require_http_methods(["DELETE", "POST"])
@csrf_exempt
@role(UserRole.PROPRIETAIRE)
def gerer_habilitation(request, id: int):
    habilitation = get_object_or_404(Habilitation, pk=id)

    # Vérification critique de sécurité : l'habilitation doit appartenir
    # à l'entreprise courante en session
    siren_session = request.session.get("entreprise")
    if habilitation.entreprise.siren != siren_session:
        return HttpResponseForbidden(
            "Cette habilitation n'appartient pas à l'entreprise courante."
        )

    if habilitation.user.pk == request.user.pk:
        return HttpResponseBadRequest(
            "Un utilisateur ne peut pas modifier une de ses habilitations"
        )

    match request.method:
        case "POST":
            habilitation.role = request.POST.get("role")
            habilitation.save()
            messages.success(
                request,
                f"L'habilitation de {habilitation.user.prenom} {habilitation.user.nom} a été modifiée ({habilitation.get_role_display()})",
            )
        case "DELETE":
            try:
                habilitation.delete()
            except HabilitationError as err:
                messages.error(request, str(err))
                return

            messages.success(
                request,
                f"L'habilitation de {habilitation.user.prenom} {habilitation.user.nom} a été supprimée",
            )
        case _:
            # normallement filtré en amont par le filtre de type de requêtes
            # mais plus propre...
            return HttpResponseBadRequest()

    # 303 nécessaire (changement de méthode)
    return HttpResponseRedirectSeeOther(
        reverse(
            "reglementations:tableau_de_bord",
            args=[request.session["entreprise"]],
        )
    )
