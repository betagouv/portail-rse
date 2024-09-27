from django.urls import path

from .enjeux import selection_enjeux

urlpatterns = [
    path(
        "csrd/fragments/selection_enjeux/<str:csrd_id>/<str:esrs>",
        selection_enjeux,
        name="selection_enjeux",
    ),
]
