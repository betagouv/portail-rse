from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group

from habilitations.admin import HabilitationInline
from users.forms import UserChangeForm
from users.forms import UserCreationForm
from users.models import User


class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm

    readonly_fields = ("last_login",)
    list_display = ("email", "is_staff")
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
    search_fields = ("email",)
    ordering = ("email",)
    filter_horizontal = ()
    inlines = (HabilitationInline,)


admin.site.register(User, UserAdmin)
admin.site.unregister(Group)
