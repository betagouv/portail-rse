from django.urls import path
from django.urls import re_path
from django.urls.conf import include

from reglementations import views
from reglementations.views import anticipation
from reglementations.views import tableau_de_bord

app_name = "reglementations"
urlpatterns = [
    path(
        "tableau-de-bord/",
        tableau_de_bord.tableau_de_bord,
        name="tableau_de_bord",
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
        tableau_de_bord.rapport_generique,
        name="rapport_generique",
    ),
    path(
        "tableau-de-bord/<uuid:id_public>/rapport/",
        tableau_de_bord.rapport,
        name="rapport",
    ),
    path(
        "tableau-de-bord/<uuid:id_public>/rapport/analyse-double-materialite",
        tableau_de_bord.analyse_double_materialite,
        name="analyse_double_materialite",
    ),
    path(
        "tableau-de-bord/<uuid:id_public>/",
        tableau_de_bord.tableau_de_bord,
        name="tableau_de_bord",
    ),
    re_path(
        r"^tableau-de-bord/(?P<siren>\d{9})/$",
        tableau_de_bord.redirection_tableau_de_bord_par_siren,
    ),
    path(
        "tableau-de-bord/<uuid:id_public>/reglementations/index/",
        tableau_de_bord.index,
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
        anticipation.anticiper,
        name="anticipation",
    ),
    path(
        "bdese/<uuid:id_public>/<int:annee>/<int:step>",
        views.bdese.bdese_step,
        name="bdese_step",
    ),
    path(
        "bdese/<uuid:id_public>/<int:annee>/pdf",
        views.bdese.bdese_pdf,
        name="bdese_pdf",
    ),
    path(
        "bdese/<uuid:id_public>/<int:annee>/actualiser-desactualiser",
        views.bdese.toggle_bdese_completion,
        name="toggle_bdese_completion",
    ),
]

# csrd
urlpatterns += [path("", include("reglementations.views.csrd.urls"))]
