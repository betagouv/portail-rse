from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMessage
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse

from .enums import UserRole
from .forms import InvitationForm
from .models import Habilitation
from entreprises.models import Entreprise
from invitations.models import Invitation
from users.models import User
from utils.tokens import make_token


@login_required()
def index(request, siren):
    entreprise = get_object_or_404(Entreprise, siren=siren)
    request.session["entreprise"] = siren
    if request.POST:
        form = InvitationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            try:
                utilisateur = User.objects.get(email=email)
                if Habilitation.objects.filter(entreprise=entreprise, user=utilisateur):
                    messages.error(
                        request,
                        "L'invitation a échoué car cette personne est déjà membre de l'entreprise.",
                    )
                else:
                    _ajoute_membre(request, entreprise, utilisateur)
            except ObjectDoesNotExist:
                _cree_invitation(request, entreprise, email)
            return redirect(
                reverse("habilitations:membres_entreprise", args=[entreprise.siren])
            )
        else:
            messages.error(
                request,
                "L'invitation a échoué car le formulaire contient des erreurs.",
            )
            context = {
                "form": form,
            }
    else:
        context = {
            "form": InvitationForm(),
        }

    context.update(
        {
            "entreprise": entreprise,
            "habilitation": Habilitation.pour(entreprise, request.user),
            "invitations": Invitation.objects.filter(
                entreprise=entreprise, date_acceptation__isnull=True
            ),
        }
    )
    # organisation des membres par habilitations
    habilitations = []
    for h in entreprise.habilitation_set.all().order_by("user__nom"):
        if h.entreprise == entreprise and h.user.is_email_confirmed:
            habilitations.append(h)

    context |= {"habilitations": habilitations}

    return render(request, "habilitations/membres.html", context)


def _ajoute_membre(request, entreprise, utilisateur):
    invitation = Invitation.objects.create(
        entreprise=entreprise,
        email=utilisateur.email,
        role=UserRole.PROPRIETAIRE.value,
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


def _cree_invitation(request, entreprise, email):
    invitation = Invitation.objects.create(
        entreprise=entreprise,
        email=email,
        role=UserRole.PROPRIETAIRE.value,
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
    }
    email.send()
