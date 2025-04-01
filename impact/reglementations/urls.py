from django.urls import path
from django.urls.conf import include

from reglementations import views

app_name = "reglementations"
urlpatterns = [
    path(
        "tableau-de-bord",
        views.tableau_de_bord,
        name="tableau_de_bord",
    ),
    path(
        "tableau-de-bord/<str:siren>",
        views.tableau_de_bord,
        name="tableau_de_bord",
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
