from django.urls import path

from . import views

urlpatterns = [
    path("exemple-formulaire/", views.exemple_formulaire, name="exemple_formulaire"),
]
