from django.conf import settings
from django_hosts import host
from django_hosts import patterns

# Two (virtual) hosts defined : admin and actual site.
# Just don't forget to update ALLOWED_HOSTS in the settings.

host_patterns = patterns(
    "",
    # first, be specific : check if we want to access to the admin site:
    host(rf"{settings.ADMIN_CNAME}", "impact.admin_urls", name="admin"),
    # otherwise, use a catch-all regexp to point to the actual site:
    host(r"(\w+)", settings.ROOT_URLCONF, name="site"),
)
