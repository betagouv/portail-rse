from django.urls import path

from habilitations import views

app_name = "habilitations"
urlpatterns = [
    path(
        "droits/<str:siren>",
        views.index,
        name="membres_entreprise",
    ),
]
