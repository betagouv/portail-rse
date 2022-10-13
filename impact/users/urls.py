from django.contrib.auth import views as auth_views
from django.urls import path

from .forms import LoginForm, PasswordResetForm, SetPasswordForm
from . import views

urlpatterns = [
    path(
        "connexion",
        auth_views.LoginView.as_view(
            template_name="users/login.html", authentication_form=LoginForm
        ),
        name="login",
    ),
    path("deconnexion", auth_views.LogoutView.as_view(), name="logout"),
    path("creation", views.creation, name="creation"),
    path(
        "mot-de-passe",
        auth_views.PasswordResetView.as_view(
            template_name="users/password_reset_form.html",
            form_class=PasswordResetForm,
            email_template_name="users/email/password_reset_email.html",
            subject_template_name="users/email/password_reset_subject.txt",
            success_url="/",
            # on pourrait faire une page de confirmation d'email envoyé à la place de success_url
        ),
        name="password_reset",
    ),
    path(
        "mot-de-passe/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="users/password_reset_confirm.html",
            form_class=SetPasswordForm,
            # success_url="login",
            # ne fonctionne pas alors que ça devrait ? du coup on utilise password_reset_complete ci-dessous
        ),
        name="password_reset_confirm",
    ),
    path(
        "mot-de-passe/reinitialise",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="users/password_reset_complete.html"
        ),
        name="password_reset_complete",
    )
    # non nécessaire si success_url fonctionne
]
