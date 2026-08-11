from django.urls import path
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
        "tableau-de-bord/<str:siren>/rapport/",
        tableau_de_bord.rapport,
        name="rapport",
    ),
    path(
        "tableau-de-bord/<str:siren>/rapport/analyse-double-materialite",
        tableau_de_bord.analyse_double_materialite,
        name="analyse_double_materialite",
    ),
    path(
        "tableau-de-bord/<str:siren>/",
        tableau_de_bord.tableau_de_bord,
        name="tableau_de_bord",
    ),
    path(
        "tableau-de-bord/<str:siren>/reglementations/index/",
        tableau_de_bord.index,
        name="index",
    ),
    path(
        "tableau-de-bord/<str:siren>/reglementations/",
        views.reglementations,
        name="reglementations",
    ),
    path(
        "tableau-de-bord/<str:siren>/reglementations/<str:id_reglementation>/",
        views.reglementation,
        name="reglementation",
    ),
    path(
        "tableau-de-bord/<str:siren>/anticipation/",
        anticipation.anticiper,
        name="anticipation",
    ),
    path(
        "bdese/<str:siren>/<int:annee>/<int:step>",
        views.bdese.bdese_step,
        name="bdese_step",
    ),
    path("bdese/<str:siren>/<int:annee>/pdf", views.bdese.bdese_pdf, name="bdese_pdf"),
    path(
        "bdese/<str:siren>/<int:annee>/actualiser-desactualiser",
        views.bdese.toggle_bdese_completion,
        name="toggle_bdese_completion",
    ),
]

# csrd
urlpatterns += [path("", include("reglementations.views.csrd.urls"))]
