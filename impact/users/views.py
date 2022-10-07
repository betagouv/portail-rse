from django.shortcuts import render

from .forms import UserCreationForm


def creation(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
    else:
        form = UserCreationForm()
    return render(request, "users/creation.html", {"form": form})
