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
    list_display = ("id", "email", "is_staff", "uidb64")
    list_filter = ("is_staff",)
    search_fields = ["id"]
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
    search_fields = ("email", "entreprise__denomination")
    ordering = ("email",)
    filter_horizontal = ()
    inlines = (HabilitationInline,)

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(
            request, queryset, search_term
        )
        PREFIXE_IDS = "ids:"
        if search_term.startswith(PREFIXE_IDS):
            longueur_prefixe = len(PREFIXE_IDS)
            ids_term = search_term[longueur_prefixe:]
            ids = [int(id) for id in ids_term.split(" ") if id]
            queryset |= self.model.objects.filter(id__in=ids)
        return queryset.distinct(), use_distinct


admin.site.register(User, UserAdmin)
admin.site.unregister(Group)
