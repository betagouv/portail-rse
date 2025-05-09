from collections import defaultdict

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse

from .enums import UserRole
from .forms import InvitationForm
from .models import Habilitation
from entreprises.models import Entreprise
from invitations.models import cree_code_invitation
from invitations.models import Invitation


@login_required()
def index(request, siren):
    entreprise = get_object_or_404(Entreprise, siren=siren)
    if request.POST:
        form = InvitationForm(request.POST)
        email = form.cleaned_data["email"]
        invitation = Invitation.objects.create(
            entreprise=entreprise,
            email=email,
            code=cree_code_invitation(),
            role=UserRole.PROPRIETAIRE.value,
        )
        _envoi_email_d_invitation(request, invitation)
        messages.success(
            request,
            "L'invitation a été envoyée.",
        )
        return redirect(
            reverse("habilitations:membres_entreprise", args=[entreprise.siren])
        )
    context = {
        "entreprise": entreprise,
        "habilitation": Habilitation.pour(entreprise, request.user),
        "invitations": Invitation.objects.filter(entreprise=entreprise),
        "form": InvitationForm(),
    }

    # organisation des membres par habilitations
    habilitations = defaultdict(list)
    for h in entreprise.habilitation_set.all().order_by("user__nom"):
        if h.entreprise == entreprise:
            habilitations[h.role].append(h.user)

    context |= {"habilitations": habilitations}

    return render(request, "habilitations/membres.html", context)


def _envoi_email_d_invitation(request, invitation):
    email = EmailMessage(
        to=[invitation.email],
        from_email=settings.DEFAULT_FROM_EMAIL,
    )
    email.template_id = settings.BREVO_INVITATION_TEMPLATE
    path = reverse(
        "users:invitation",
    )
    url = f"{request.build_absolute_uri(path)}?invitation={invitation.id}&code={invitation.code}"
    email.merge_global_data = {
        "denomination_entreprise": invitation.entreprise.denomination,
        "invitation_url": url,
    }
    email.send()
