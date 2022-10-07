from django.contrib.auth import login
from django.shortcuts import redirect, render

from .forms import UserCreationForm
from .models import User


def creation(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            login(request, User.objects.get(email=form.cleaned_data["email"]))
            return redirect("bdese", siren=form.cleaned_data["siren"])
    else:
        form = UserCreationForm()
    return render(request, "users/creation.html", {"form": form})
