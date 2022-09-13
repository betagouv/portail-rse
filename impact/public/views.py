from django.shortcuts import render


def index(request):
    return render(request, "public/index.html")


def siren(request):
    siren = request.GET["siren"]
    return render(request, "public/siren.html", {"siren": siren})
