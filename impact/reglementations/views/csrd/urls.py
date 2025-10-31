from django.urls import path
from django.urls.conf import include

from reglementations.views.csrd.csrd import datapoints_xlsx
from reglementations.views.csrd.csrd import enjeux_materiels_xlsx
from reglementations.views.csrd.csrd import enjeux_xlsx
from reglementations.views.csrd.csrd import gestion_csrd

urlpatterns = [
    path(
        "csrd/etape-<str:id_etape>",
        gestion_csrd,
        name="gestion_csrd",
    ),
    path(
        "csrd/<str:siren>/etape-<str:id_etape>",
        gestion_csrd,
        name="gestion_csrd",
    ),
    path("csrd/<str:siren>/enjeux.xlsx", enjeux_xlsx, name="enjeux_xlsx"),
    path(
        "csrd/<str:siren>/enjeux_materiels.xlsx",
        enjeux_materiels_xlsx,
        name="enjeux_materiels_xlsx",
    ),
    path(
        "csrd/<str:siren>/datapoints.xlsx",
        datapoints_xlsx,
        name="datapoints_xlsx",
    ),
]

# Fragments HTMX
urlpatterns += [path("", include("reglementations.views.csrd.fragments.urls"))]
