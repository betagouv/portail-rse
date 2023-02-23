from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import EntrepriseCreationForm
from .models import Entreprise, Habilitation

@login_required()
def index(request):
    form = EntrepriseCreationForm()
    return render(request, "entreprises/index.html", {"form": form})

@login_required()
def add(request):
    form = EntrepriseCreationForm(request.POST)
    if form.is_valid():
        siren = form.cleaned_data["siren"]
        if entreprises := Entreprise.objects.filter(siren=siren):
            entreprise = entreprises[0]
        else:
            entreprise = Entreprise.objects.create(siren=siren)
        Habilitation.objects.create(
            user=request.user,
            entreprise=entreprise,
        )
        success_message = "L'entreprise a été ajoutée."
        messages.success(request, success_message)
        return redirect("entreprises")
    else:
        messages.error(request, "Impossible de créer l'entreprise car les données sont incorrectes.")
        return render(request, "entreprises/index.html", {"form": form})