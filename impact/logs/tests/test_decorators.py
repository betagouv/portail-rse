import logging

import pytest
from django.contrib.sessions.backends.db import SessionStore
from django.http import HttpResponse
from django.test import RequestFactory

from logs.decorators import log_path
from logs.models import EventLog


@pytest.mark.django_db
def test_log_path_utilisateur_authentifie(alice):
    @log_path("page:test_auth")
    def ma_vue(_):
        return HttpResponse("OK")

    factory = RequestFactory()
    request = factory.get("/test/")
    request.user = alice
    request.session = SessionStore()
    request.session["entreprise"] = "123456789"
    request.session.save()

    ma_vue(request)

    events = EventLog.objects.all()
    assert events.count() == 1

    event = events.first()
    assert event.level == logging.INFO
    assert event.msg == "page:test_auth"
    assert event.payload["idUtilisateur"] == alice.pk
    assert event.payload["siren"] == "123456789"
    assert event.payload["session"] == request.session.session_key


@pytest.mark.django_db
def test_log_path_utilisateur_anonyme():
    @log_path("page:test_anonyme")
    def ma_vue(_):
        return HttpResponse("OK")

    factory = RequestFactory()
    request = factory.get("/test/")
    from django.contrib.auth.models import AnonymousUser

    request.user = AnonymousUser()
    request.session = SessionStore()
    request.session.save()

    ma_vue(request)

    # Utilisateur anonyme mais session présente : un log est créé avec session_key
    events = EventLog.objects.all()
    assert events.count() == 1

    event = events.first()
    assert event.msg == "page:test_anonyme"
    assert "idUtilisateur" not in event.payload
    assert "siren" not in event.payload
    assert event.payload["session"] == request.session.session_key


@pytest.mark.django_db
def test_log_path_avec_siren_sans_utilisateur():
    @log_path("page:test_siren_only")
    def ma_vue(_):
        return HttpResponse("OK")

    factory = RequestFactory()
    request = factory.get("/test/")
    from django.contrib.auth.models import AnonymousUser

    request.user = AnonymousUser()
    request.session = SessionStore()
    request.session["entreprise"] = "987654321"
    request.session.save()

    ma_vue(request)

    events = EventLog.objects.all()
    assert events.count() == 1

    event = events.first()
    assert event.msg == "page:test_siren_only"
    assert "idUtilisateur" not in event.payload
    assert event.payload["siren"] == "987654321"
    assert event.payload["session"] == request.session.session_key


@pytest.mark.django_db
def test_log_path_sans_session():
    @log_path("page:test_no_session")
    def ma_vue(_):
        return HttpResponse("OK")

    factory = RequestFactory()
    request = factory.get("/test/")
    from django.contrib.auth.models import AnonymousUser

    request.user = AnonymousUser()
    # Pas de session assignée

    ma_vue(request)

    # Pas de session, pas de log
    assert EventLog.objects.count() == 0


@pytest.mark.django_db
def test_log_path_session_sans_siren(alice):
    @log_path("page:test_no_siren")
    def ma_vue(_):
        return HttpResponse("OK")

    factory = RequestFactory()
    request = factory.get("/test/")
    request.user = alice
    request.session = SessionStore()
    request.session.save()

    ma_vue(request)

    events = EventLog.objects.all()
    assert events.count() == 1

    event = events.first()
    assert event.msg == "page:test_no_siren"
    assert event.payload["idUtilisateur"] == alice.pk
    assert "siren" not in event.payload
    assert event.payload["session"] == request.session.session_key


@pytest.mark.django_db
def test_log_path_vue_executee_correctement(alice):
    @log_path("page:test_execution")
    def ma_vue(_):
        return HttpResponse("Response content")

    factory = RequestFactory()
    request = factory.get("/test/")
    request.user = alice
    request.session = SessionStore()
    request.session.save()

    response = ma_vue(request)

    # La vue a été exécutée
    assert response.status_code == 200
    assert response.content == b"Response content"

    # Le log a été créé
    assert EventLog.objects.count() == 1


@pytest.mark.django_db
def test_log_path_vue_avec_arguments(alice):
    @log_path("page:test_args")
    def ma_vue(request, article_id, slug=None):
        return HttpResponse(f"Article {article_id} - {slug}")

    factory = RequestFactory()
    request = factory.get("/test/")
    request.user = alice
    request.session = SessionStore()
    request.session["entreprise"] = "111222333"
    request.session.save()

    response = ma_vue(request, article_id=42, slug="mon-article")

    # La vue a été exécutée avec les bons arguments
    assert response.content == b"Article 42 - mon-article"

    # Le log a été créé
    events = EventLog.objects.all()
    assert events.count() == 1

    event = events.first()
    assert event.msg == "page:test_args"
    assert event.payload["idUtilisateur"] == alice.pk
    assert event.payload["siren"] == "111222333"


@pytest.mark.django_db
def test_log_path_messages_differents(alice):
    @log_path("page:accueil")
    def vue_accueil(request):
        return HttpResponse("Accueil")

    @log_path("page:contact")
    def vue_contact(request):
        return HttpResponse("Contact")

    factory = RequestFactory()
    request = factory.get("/test/")
    request.user = alice
    request.session = SessionStore()
    request.session.save()

    vue_accueil(request)
    vue_contact(request)

    events = EventLog.objects.all().order_by("created_at")
    assert events.count() == 2

    assert events[0].msg == "page:accueil"
    assert events[1].msg == "page:contact"


@pytest.mark.django_db
def test_log_path_preserve_nom_fonction(alice):
    @log_path("page:test")
    def ma_vue_originale(request):
        return HttpResponse("OK")

    # Le décorateur utilise @wraps, donc le nom est préservé
    assert ma_vue_originale.__name__ == "ma_vue_originale"


@pytest.mark.django_db
def test_log_path_session_key_none():
    @log_path("page:test_no_key")
    def ma_vue(_):
        return HttpResponse("OK")

    factory = RequestFactory()
    request = factory.get("/test/")
    from django.contrib.auth.models import AnonymousUser

    request.user = AnonymousUser()
    request.session = SessionStore()
    # Session créée mais pas encore sauvegardée, donc pas de session_key
    # Ne pas appeler request.session.save()

    ma_vue(request)

    # Pas de session_key, pas de log
    assert EventLog.objects.count() == 0


@pytest.mark.django_db
def test_log_path_utilisateur_sans_attribut_user():
    @log_path("page:test_no_user")
    def ma_vue(_):
        return HttpResponse("OK")

    factory = RequestFactory()
    request = factory.get("/test/")
    # Pas d'attribut user assigné
    request.session = SessionStore()
    request.session["entreprise"] = "123456789"
    request.session.save()

    ma_vue(request)

    # Pas d'utilisateur mais SIREN présent
    events = EventLog.objects.all()
    assert events.count() == 1

    event = events.first()
    assert "idUtilisateur" not in event.payload
    assert event.payload["siren"] == "123456789"


@pytest.mark.django_db
def test_log_path_tous_champs_presents(alice):
    @log_path("page:complet")
    def ma_vue(_):
        return HttpResponse("OK")

    factory = RequestFactory()
    request = factory.get("/test/")
    request.user = alice
    request.session = SessionStore()
    request.session["entreprise"] = "555666777"
    request.session.save()

    ma_vue(request)

    event = EventLog.objects.first()
    assert event.msg == "page:complet"

    # Tous les champs sont présents
    assert "idUtilisateur" in event.payload
    assert "siren" in event.payload
    assert "session" in event.payload

    assert event.payload["idUtilisateur"] == alice.pk
    assert event.payload["siren"] == "555666777"
    assert event.payload["session"] is not None


@pytest.mark.django_db
def test_log_path_vue_qui_leve_exception(alice):
    @log_path("page:test_exception")
    def ma_vue(_):
        raise ValueError("Erreur test")

    factory = RequestFactory()
    request = factory.get("/test/")
    request.user = alice
    request.session = SessionStore()
    request.session.save()

    # L'exception doit se propager
    with pytest.raises(ValueError, match="Erreur test"):
        ma_vue(request)

    # Le log a été créé avant l'exception
    assert EventLog.objects.count() == 1


@pytest.mark.django_db
def test_log_path_multiples_appels_meme_vue(alice, bob):
    @log_path("page:dashboard")
    def dashboard(request):
        return HttpResponse("Dashboard")

    factory = RequestFactory()

    # Premier appel avec alice
    request1 = factory.get("/dashboard/")
    request1.user = alice
    request1.session = SessionStore()
    request1.session["entreprise"] = "111111111"
    request1.session.save()
    dashboard(request1)

    # Deuxième appel avec bob
    request2 = factory.get("/dashboard/")
    request2.user = bob
    request2.session = SessionStore()
    request2.session["entreprise"] = "222222222"
    request2.session.save()
    dashboard(request2)

    events = EventLog.objects.all().order_by("created_at")
    assert events.count() == 2

    # Premier log pour alice
    assert events[0].payload["idUtilisateur"] == alice.pk
    assert events[0].payload["siren"] == "111111111"

    # Deuxième log pour bob
    assert events[1].payload["idUtilisateur"] == bob.pk
    assert events[1].payload["siren"] == "222222222"
