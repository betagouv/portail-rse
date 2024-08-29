from django.contrib import admin
from django.urls import path

# URLs / path for the admin site

urlpatterns = [
    path("", admin.site.urls),
]
