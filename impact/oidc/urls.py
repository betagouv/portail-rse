"""Routage spécifique pour une identification ProConnect"""

from django.urls import path
from lasuite.oidc_login.urls import urlpatterns as lasuite_oidc_urls

from .views import dispatch_view

urlpatterns = [
    path("dispatch/", dispatch_view, name="oidc_dispatch"),
    *lasuite_oidc_urls,
]
