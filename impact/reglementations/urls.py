from django.urls import path
from django.urls.conf import include

from reglementations import views

app_name = "reglementations"
urlpatterns = [
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
