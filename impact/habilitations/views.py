from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from entreprises.models import Entreprise


@login_required()
def index(request, siren):
    entreprise = Entreprise.objects.get(siren=siren)
    return render(request, "habilitations/membres.html", {"entreprise": entreprise})
