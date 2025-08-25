from django.shortcuts import render

from .factory import create_form_from_yaml
from .factory import load_yaml_schema


def exemple_formulaire(request):
    yaml_data = load_yaml_schema("defs/exemple.yml")
    form = create_form_from_yaml(yaml_data)()

    if request.method == "POST":
        form = create_form_from_yaml(yaml_data)(request.POST)
        if form.is_valid():
            print("cleaned_data:", form.cleaned_data)

    return render(request, "exemple_formulaire.html", {"form": form})
