from django.urls import path
from django.urls import re_path

from tableau_de_bord import views

app_name = "tableau_de_bord"
urlpatterns = [
    path(
        "tableau-de-bord/",
        views.resume,
        name="resume",
    ),
    path(
        "tableau-de-bord/reglementations/",
        views.reglementations,
        name="reglementations",
    ),
    path(
        "tableau-de-bord/reglementations/<str:id_reglementation>/",
        views.reglementation,
        name="reglementation",
    ),
    path(
        "tableau-de-bord/rapport/",
        views.rapport_generique,
        name="rapport_generique",
    ),
    path(
        "tableau-de-bord/<uuid:id_public>/rapport/",
        views.rapport,
        name="rapport",
    ),
    path(
        "tableau-de-bord/<uuid:id_public>/rapport/analyse-double-materialite",
        views.analyse_double_materialite,
        name="analyse_double_materialite",
    ),
    path(
        "tableau-de-bord/<uuid:id_public>/",
        views.resume,
        name="resume",
    ),
    re_path(
        r"^tableau-de-bord/(?P<siren>\d{9})/$",
        views.redirection_tableau_de_bord_par_siren,
    ),
    path(
        "tableau-de-bord/<uuid:id_public>/reglementations/index/",
        views.index,
        name="index",
    ),
    path(
        "tableau-de-bord/<uuid:id_public>/reglementations/",
        views.reglementations,
        name="reglementations",
    ),
    path(
        "tableau-de-bord/<uuid:id_public>/reglementations/<str:id_reglementation>/",
        views.reglementation,
        name="reglementation",
    ),
    path(
        "tableau-de-bord/<uuid:id_public>/anticipation/",
        views.anticiper,
        name="anticipation",
    ),
    path(
        "tableau-de-bord-conseiller",
        views.conseiller,
        name="conseiller",
    ),
]
