from django.urls import path

from habilitations import views

app_name = "habilitations"
urlpatterns = [
    path(
        "invitation/<str:siren>",
        views.invitation,
        name="invitation",
    ),
    # fragments / snippets
    path("habilitation/<int:id>", views.gerer_habilitation, name="gerer_habilitation"),
]
