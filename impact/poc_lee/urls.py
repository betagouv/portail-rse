from django.urls import path

import poc_lee.views as views

app_name = "poc_lee"
urlpatterns = [
    path(
        "poc-lee/entreprises/<str:siren>/obligations",
        views.obligations,
        name="obligations",
    ),
    path(
        "poc-lee/entreprises/<str:siren>/vsme/preremplissages",
        views.preremplissages,
        name="preremplissages",
    ),
]
