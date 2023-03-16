from django.urls import path

from . import views

app_name = "entreprises"
urlpatterns = [
    path("entreprises", views.index, name="entreprises"),
    path("entreprises/add", views.add, name="add"),
    path("entreprises/<str:siren>", views.qualification, name="qualification"),
    path("api/search-entreprise/<str:siren>", views.search_entreprise),
]
