from collections import defaultdict

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.shortcuts import render

from .models import Habilitation
from entreprises.models import Entreprise


@login_required()
def index(request, siren):
    entreprise = get_object_or_404(Entreprise, siren=siren)
    context = {
        "entreprise": entreprise,
        "habilitation": Habilitation.pour(entreprise, request.user),
    }

    # organisation des membres par habilitations
    habilitations = defaultdict(list)
    for h in entreprise.habilitation_set.all().order_by("user__nom"):
        if h.entreprise == entreprise:
            habilitations[h.role].append(h.user)

    context |= {"habilitations": habilitations}

    return render(request, "habilitations/membres.html", context)
