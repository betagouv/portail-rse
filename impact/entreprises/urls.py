from django.urls import path

from . import views

urlpatterns = [
    path("entreprises", views.index, name="entreprises"),
    path("entreprises/add", views.add, name="add_entreprise"),
    path("entreprises/<str:siren>", views.detail_entreprise, name="detail_entreprise"),
    path("api/search-entreprise/<str:siren>", views.search_entreprise),
]
