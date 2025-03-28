from django.conf import settings
from django.http.request import HttpRequest
from django.template import Context
from django.template import Template


def test_tag_absolute_url(client):
    request = HttpRequest()
    SERVER_NAME = settings.ALLOWED_HOSTS[0]
    request.META = {"SERVER_NAME": SERVER_NAME, "SERVER_PORT": 80}

    out = Template("{% load absolute_url %}{% absolute_url 'stats' %}").render(
        Context({"request": request})
    )

    assert out == f"http://{SERVER_NAME}/stats"


def test_tag_absolute_url_si_erreur_dans_le_service(client):
    """Si une exception survient dans l'application, l'objet Context ne contient plus la requête.
    Dans ce cas, le service django boucle car en cas de l'erreur, le contexte n'est pas complet,
    ce qui lève une KeyError, que Django attrape et tente d'afficher une erreur, qui a l'air d'avoir besoin de absolute_url, etc.

    Ce problème est visible dans les tests unitaires.
    """
    request = HttpRequest()
    SERVER_NAME = settings.ALLOWED_HOSTS[0]
    request.META = {"SERVER_NAME": SERVER_NAME, "SERVER_PORT": 80}

    out = Template("{% load absolute_url %}{% absolute_url 'stats' %}").render(
        Context({})
    )

    assert out == ""
