from urllib.parse import quote

import geojson
from django import template


register = template.Library()


@register.simple_tag
def url_geolocalisation(coordonnees_str):
    coordonnees = geojson.loads(coordonnees_str)
    point = geojson.Point(coordonnees)
    polygon = geojson.Polygon(coordonnees)
    if point.is_valid:
        geojson_data = geojson.dumps(point, sort_keys=True)
    elif polygon.is_valid:
        geojson_data = geojson.dumps(polygon, sort_keys=True)
    url = f"http://geojson.io/#data=data:application/json,{quote(geojson_data)}"
    return url
