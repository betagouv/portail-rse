from django.urls import path

from . import views

urlpatterns = [
    path("reglementations", views.reglementations, name="reglementations"),
    path("bdese/<str:siren>", views.bdese, name="bdese"),
    path("bdese/<str:siren>/result", views.bdese_result, name="bdese_result"),
]
