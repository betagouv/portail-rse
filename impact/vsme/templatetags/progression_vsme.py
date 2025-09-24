from django import template

register = template.Library()


@register.simple_tag
def progression_exigence(rapport_vsme, exigence_de_publication):
    return rapport_vsme.progression_par(exigence_de_publication)
