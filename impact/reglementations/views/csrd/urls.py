from django.urls import path
from django.urls import re_path
from django.urls.conf import include

from reglementations.views.csrd.csrd import datapoints_xlsx
from reglementations.views.csrd.csrd import enjeux_materiels_xlsx
from reglementations.views.csrd.csrd import enjeux_xlsx
from reglementations.views.csrd.csrd import gestion_csrd
from reglementations.views.csrd.csrd import redirection_analyse_ecart_par_siren

urlpatterns = [
    path(
        "csrd/etape-<str:id_etape>",
        gestion_csrd,
        name="gestion_csrd",
    ),
    path(
        "csrd/<uuid:id_public>/etape-<str:id_etape>",
        gestion_csrd,
        name="gestion_csrd",
    ),
    path("csrd/<uuid:id_public>/enjeux.xlsx", enjeux_xlsx, name="enjeux_xlsx"),
    path(
        "csrd/<uuid:id_public>/enjeux_materiels.xlsx",
        enjeux_materiels_xlsx,
        name="enjeux_materiels_xlsx",
    ),
    path(
        "csrd/<uuid:id_public>/datapoints.xlsx",
        datapoints_xlsx,
        name="datapoints_xlsx",
    ),
    re_path(
        r"^csrd/(?P<siren>\d{9})/etape-analyse-ecart$",
        redirection_analyse_ecart_par_siren,
    ),
]

# Fragments HTMX
urlpatterns += [path("", include("reglementations.views.csrd.fragments.urls"))]
