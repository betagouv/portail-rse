from django.urls import path

from . import views

urlpatterns = [
    path("reglementations", views.reglementations, name="reglementations"),
    path("bdese/<str:siren>/<int:step>", views.bdese, name="bdese"),
    path("bdese/<str:siren>/pdf", views.bdese_pdf, name="bdese_pdf"),
]
