from uuid import uuid4

from django import template

register = template.Library()


@register.simple_tag
def uuid():
    return str(uuid4())
