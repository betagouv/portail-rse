from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordResetView as BasePasswordResetView
from django.contrib.auth.views import (
    PasswordResetConfirmView as BasePasswordResetConfirmView,
)
from django.shortcuts import redirect, render

from .forms import UserCreationForm, UserEditionForm
from .models import User


def creation(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            login(request, User.objects.get(email=form.cleaned_data["email"]))
            success_message = (
                "Votre compte a bien été créé. Vous êtes maintenant connecté."
            )
            messages.success(request, success_message)
            siren = form.cleaned_data["siren"]
            return redirect("reglementation", siren)
        else:
            messages.error(
                request, "La création a échoué car le formulaire contient des erreurs."
            )
    else:
        siren = request.session.get("siren")
        form = UserCreationForm(initial={"siren": siren})
    return render(request, "users/creation.html", {"form": form})


@login_required()
def account(request):
    form = UserEditionForm(request.POST or None, instance=request.user)
    if form.is_valid():
        form.save()
        if "password1" in form.changed_data:
            success_message = (
                "Votre mot de passe a bien été modifié. Veuillez vous reconnecter."
            )
        else:
            success_message = "Votre compte a bien été modifié."
        messages.success(request, success_message)
        return redirect("account")
    elif request.POST:
        error_message = (
            "La modification a échoué car le formulaire contient des erreurs."
        )
        messages.error(request, error_message)
    return render(request, "users/account.html", {"form": form})


class PasswordResetView(BasePasswordResetView):
    def form_valid(self, form):
        response = super(PasswordResetView, self).form_valid(form)
        success_message = "Un lien de ré-initialisation de votre mot de passe vous a été envoyé par mail. Vous devriez le recevoir d'ici quelques minutes."
        messages.success(self.request, success_message)
        return response


class PasswordResetConfirmView(BasePasswordResetConfirmView):
    def form_valid(self, form):
        response = super(PasswordResetConfirmView, self).form_valid(form)
        success_message = "Votre mot de passe a été réinitialisé avec succès. Vous pouvez à présent vous connecter."
        messages.success(self.request, success_message)
        return response
