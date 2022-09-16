from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("siren", views.siren, name="siren"),
    path("eligibilite", views.eligibilite, name="eligibilite"),
    path("result", views.result, name="result"),
]
