from django.urls import path

import vsme.views as views

app_name = "vsme"
urlpatterns = [
    path(
        "vsme/<str:siren>/<str:etape>/",
        views.etape_vsme,
        name="etape_vsme",
    ),
]
