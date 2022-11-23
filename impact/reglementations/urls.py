from django.urls import path

from . import views

urlpatterns = [
    path("reglementations", views.reglementations, name="reglementations"),
    path("bdese/<str:siren>/annees", views.bdese_annees, name="bdese_annees"),
    path("bdese/<str:siren>/<int:annee>/<int:step>", views.bdese, name="bdese"),
    path("bdese/<str:siren>/pdf", views.bdese_pdf, name="bdese_pdf"),
]
