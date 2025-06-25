from django.contrib import admin

from invitations.models import Invitation


class InvitationAdmin(admin.ModelAdmin):
    list_display = ["entreprise", "email"]
    raw_id_fields = ("entreprise", "inviteur")
    model = Invitation


admin.site.register(Invitation, InvitationAdmin)
