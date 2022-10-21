from django.urls import path

from . import views

urlpatterns = [
    path("reglementations", views.reglementations, name="reglementations"),
    path("result/<str:siren>", views.result, name="result"),
    path("bdese/<str:siren>", views.bdese, name="bdese"),
]
