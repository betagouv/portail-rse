from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('/siren', views.siren, name='siren'),
]