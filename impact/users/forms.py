from django import forms
from django.contrib.auth.forms import AuthenticationForm

from public.forms import DsfrForm

class LoginForm(DsfrForm, AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        self.fields["username"].label = "Identifiant"
        self.fields["password"].label = "Mot de passe"
