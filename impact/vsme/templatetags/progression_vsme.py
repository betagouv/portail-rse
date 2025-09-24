from django import template

from vsme.models import Categorie

register = template.Library()


@register.simple_tag
def progression_exigence(rapport_vsme, exigence_de_publication):
    return rapport_vsme.progression_par_exigence(exigence_de_publication)


@register.simple_tag
def progression_categorie(rapport_vsme, categorie_id):
    categorie = Categorie.par_id(categorie_id)
    return rapport_vsme.progression_par_categorie(categorie)
