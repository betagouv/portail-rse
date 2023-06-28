from django.urls import path

from . import views


app_name = "reglementations"
urlpatterns = [
    path("reglementations", views.reglementations, name="reglementations"),
    path(
        "reglementations/<str:siren>",
        views.reglementations_for_entreprise,
        name="reglementations",
    ),
    path("bdese/<str:siren>/<int:annee>/<int:step>", views.bdese.bdese, name="bdese"),
    path("bdese/<str:siren>/<int:annee>/pdf", views.bdese.bdese_pdf, name="bdese_pdf"),
    path(
        "bdese/<str:siren>/<int:annee>/actualiser-desactualiser",
        views.bdese.toggle_bdese_completion,
        name="toggle_bdese_completion",
    ),
]
