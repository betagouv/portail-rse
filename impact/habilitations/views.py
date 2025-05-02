from collections import defaultdict

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse

from .forms import InvitationForm
from .models import Habilitation
from entreprises.models import Entreprise


@login_required()
def index(request, siren):
    entreprise = get_object_or_404(Entreprise, siren=siren)
    if request.POST:
        form = InvitationForm(request.POST)
        _envoi_email_d_invitation(request, entreprise, form.cleaned_data["email"])
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
        "form": InvitationForm(),
    }

    # organisation des membres par habilitations
    habilitations = defaultdict(list)
    for h in entreprise.habilitation_set.all().order_by("user__nom"):
        if h.entreprise == entreprise:
            habilitations[h.role].append(h.user)

    context |= {"habilitations": habilitations}

    return render(request, "habilitations/membres.html", context)


def _envoi_email_d_invitation(request, entreprise, email):
    email = EmailMessage(
        to=[email],
        from_email=settings.DEFAULT_FROM_EMAIL,
    )
    email.template_id = settings.BREVO_INVITATION_TEMPLATE
    path = reverse(
        "users:invitation",
    )
    url = f"{request.build_absolute_uri(path)}?siren={entreprise.siren}&email={email}"
    email.merge_global_data = {
        "denomination_entreprise": entreprise.denomination,
        "invitation_url": url,
    }
    email.send()
