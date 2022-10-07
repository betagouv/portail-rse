from django.contrib.auth import views as auth_views
from django.urls import path

from .forms import LoginForm


urlpatterns = [
    path(
        "connexion",
        auth_views.LoginView.as_view(
            template_name="users/login.html", authentication_form=LoginForm
        ),
        name="login",
    ),
    path("deconnexion", auth_views.LogoutView.as_view(), name="logout"),
]
