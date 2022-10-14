from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from .forms import LoginForm, PasswordResetForm, SetPasswordForm
from .views import creation, PasswordResetView, PasswordResetConfirmView

urlpatterns = [
    path(
        "connexion",
        auth_views.LoginView.as_view(
            template_name="users/login.html", authentication_form=LoginForm
        ),
        name="login",
    ),
    path("deconnexion", auth_views.LogoutView.as_view(), name="logout"),
    path("creation", creation, name="creation"),
    path(
        "mot-de-passe-oublie",
        PasswordResetView.as_view(
            template_name="users/password_reset_form.html",
            form_class=PasswordResetForm,
            email_template_name="users/email/password_reset_email.html",
            subject_template_name="users/email/password_reset_subject.txt",
            success_url="/",
        ),
        name="password_reset",
    ),
    path(
        "mot-de-passe-oublie/<uidb64>/<token>/",
        PasswordResetConfirmView.as_view(
            template_name="users/password_reset_confirm.html",
            form_class=SetPasswordForm,
            success_url=reverse_lazy("login"),
        ),
        name="password_reset_confirm",
    ),
]
