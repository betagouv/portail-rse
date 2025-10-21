from django.conf import settings
from django.contrib.auth import views as auth_views
from django.urls import path
from django.urls import reverse_lazy

from .forms import LoginForm
from .forms import PasswordResetForm
from .forms import SetPasswordForm
from .views import account
from .views import creation
from .views import deconnexion
from .views import invitation
from .views import PasswordResetConfirmView
from .views import PasswordResetView
from users.views import confirm_email

app_name = "users"

_connexion_view = auth_views.LoginView.as_view(
    template_name="users/login.html", authentication_form=LoginForm
)

# certaines options de gestion du compte et des identifiants sont absentes avec ProConnect
_creation_view = _connexion_view if settings.OIDC_ENABLED else creation

urlpatterns = [
    path(
        "connexion",
        _connexion_view,
        name="login",
    ),
    path("deconnexion", deconnexion, name="logout"),
    path("invitation/<int:id_invitation>/<str:code>", invitation, name="invitation"),
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
            success_url=reverse_lazy("users:login"),
        ),
        name="password_reset_confirm",
    ),
    path("mon-compte", account, name="account"),
    path(
        "confirme-email/<uidb64>/<token>/",
        confirm_email,
        name="confirm_email",
    ),
    path("creation", _creation_view, name="creation"),
]
