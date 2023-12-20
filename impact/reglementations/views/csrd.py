from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def csrd(request):
    return render(
        request,
        "reglementations/espace-csrd.html",
    )
