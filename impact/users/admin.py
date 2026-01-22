from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.models import Group

from habilitations.admin import HabilitationInline
from users.forms import UserPasswordForm
from users.models import User


class UserAdminChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = "__all__"


class UserAdminCreationForm(UserPasswordForm):
    class Meta:
        model = User
        fields = ("email",)


class UserAdmin(BaseUserAdmin):
    form = UserAdminChangeForm
    add_form = UserAdminCreationForm

    readonly_fields = ("last_login",)
    list_display = ("email", "is_staff", "uidb64")
    list_filter = ("is_staff",)
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "email",
                    "is_email_confirmed",
                    "password",
                    "prenom",
                    "nom",
                    "acceptation_cgu",
                    "reception_actualites",
                    "is_conseiller_rse",
                    "last_login",
                )
            },
        ),
        ("Permissions", {"fields": ("is_staff",)}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2"),
            },
        ),
    )
    search_fields = ("email", "entreprise__denomination")
    ordering = ("email",)
    filter_horizontal = ()
    inlines = (HabilitationInline,)


admin.site.register(User, UserAdmin)
admin.site.unregister(Group)
