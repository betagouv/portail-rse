from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("siren", views.siren, name="siren"),
    path("cgu", views.cgu, name="cgu"),
    path("contact", views.contact, name="contact"),
]
