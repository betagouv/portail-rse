from django.contrib import admin

from logs.models import EventLog


class EventLogAdmin(admin.ModelAdmin):
    model = EventLog
    readonly_fields = (
        "created_at",
        "msg",
        "payload",
    )


admin.site.register(EventLog, EventLogAdmin)
