import logging
from datetime import datetime
from datetime import timezone

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from logs.models import EventLog


@pytest.mark.django_db
def test_creation_event_log_basique():
    event = EventLog.objects.create(
        level=logging.INFO,
        msg="Test message",
    )

    assert event.id is not None
    assert event.level == logging.INFO
    assert event.msg == "Test message"
    assert event.payload == {}
    assert event.created_at is not None


@pytest.mark.django_db
def test_creation_event_log_avec_payload():
    payload = {
        "user_id": 123,
        "action": "login",
        "ip": "127.0.0.1",
    }

    event = EventLog.objects.create(
        level=logging.WARNING,
        msg="Tentative de connexion",
        payload=payload,
    )

    assert event.payload == payload
    assert event.payload["user_id"] == 123
    assert event.payload["action"] == "login"


@pytest.mark.django_db
def test_niveaux_logging_disponibles():
    niveaux = [
        (logging.DEBUG, "DEBUG"),
        (logging.INFO, "INFO"),
        (logging.WARNING, "WARNING"),
        (logging.ERROR, "ERROR"),
        (logging.CRITICAL, "CRITICAL"),
    ]

    for level, level_name in niveaux:
        event = EventLog.objects.create(
            level=level,
            msg=f"Message {level_name}",
        )
        assert event.level == level
        assert event.level_name == level_name


@pytest.mark.django_db
def test_level_name_property():
    event = EventLog.objects.create(
        level=logging.ERROR,
        msg="Erreur test",
    )

    assert event.level_name == "ERROR"


@pytest.mark.django_db
def test_str_representation():
    event = EventLog.objects.create(
        level=logging.INFO,
        msg="Test message",
    )

    str_repr = str(event)
    assert str(event.id) in str_repr
    assert "INFO" in str_repr


@pytest.mark.django_db
def test_repr_representation():
    payload = {"user": "alice", "action": "test"}
    event = EventLog.objects.create(
        level=logging.WARNING,
        msg="Test warning",
        payload=payload,
    )

    repr_str = repr(event)
    # Vérifie que le repr contient les éléments clés
    assert "_id" in repr_str
    assert "_msg" in repr_str
    assert "_level" in repr_str
    assert "_createdAt" in repr_str
    assert "user" in repr_str
    assert "alice" in repr_str


@pytest.mark.django_db
def test_created_at_auto_set():
    avant = datetime.now(timezone.utc)
    event = EventLog.objects.create(
        level=logging.INFO,
        msg="Test timestamp",
    )
    apres = datetime.now(timezone.utc)

    assert event.created_at is not None
    assert avant <= event.created_at <= apres


@pytest.mark.django_db
def test_created_at_timezone_aware():
    event = EventLog.objects.create(
        level=logging.INFO,
        msg="Test timezone",
    )

    assert event.created_at.tzinfo is not None


@pytest.mark.django_db
def test_payload_default_dict_vide():
    event = EventLog.objects.create(
        level=logging.INFO,
        msg="Test sans payload",
    )

    assert event.payload == {}
    assert isinstance(event.payload, dict)


@pytest.mark.django_db
def test_payload_json_complexe():
    payload = {
        "user": {"id": 123, "name": "Alice"},
        "actions": ["login", "view_page", "logout"],
        "metadata": {
            "browser": "Firefox",
            "os": "Linux",
            "nested": {"deep": "value"},
        },
        "count": 42,
        "active": True,
    }

    event = EventLog.objects.create(
        level=logging.INFO,
        msg="Action complexe",
        payload=payload,
    )

    # Récupération depuis la DB pour vérifier la sérialisation
    event_db = EventLog.objects.get(id=event.id)
    assert event_db.payload == payload
    assert event_db.payload["user"]["name"] == "Alice"
    assert len(event_db.payload["actions"]) == 3
    assert event_db.payload["metadata"]["nested"]["deep"] == "value"


@pytest.mark.django_db
def test_message_vide_autorise():
    event = EventLog.objects.create(
        level=logging.INFO,
        msg="",
    )

    assert event.msg == ""


@pytest.mark.django_db
def test_message_texte_long():
    long_message = "A" * 10000  # Message de 10000 caractères

    event = EventLog.objects.create(
        level=logging.ERROR,
        msg=long_message,
    )

    assert event.msg == long_message
    assert len(event.msg) == 10000


@pytest.mark.django_db
def test_uuid_unique_par_event():
    event1 = EventLog.objects.create(level=logging.INFO, msg="Event 1")
    event2 = EventLog.objects.create(level=logging.INFO, msg="Event 2")

    assert event1.id != event2.id
    assert isinstance(str(event1.id), str)


@pytest.mark.django_db
def test_filtrage_par_niveau():
    EventLog.objects.create(level=logging.DEBUG, msg="Debug")
    EventLog.objects.create(level=logging.INFO, msg="Info 1")
    EventLog.objects.create(level=logging.INFO, msg="Info 2")
    EventLog.objects.create(level=logging.ERROR, msg="Error")

    infos = EventLog.objects.filter(level=logging.INFO)
    assert infos.count() == 2

    errors = EventLog.objects.filter(level=logging.ERROR)
    assert errors.count() == 1


@pytest.mark.django_db
def test_ordre_chronologique():
    event1 = EventLog.objects.create(level=logging.INFO, msg="Premier")
    event2 = EventLog.objects.create(level=logging.INFO, msg="Deuxième")
    event3 = EventLog.objects.create(level=logging.INFO, msg="Troisième")

    events = EventLog.objects.all().order_by("created_at")
    events_list = list(events)

    assert events_list[0].id == event1.id
    assert events_list[1].id == event2.id
    assert events_list[2].id == event3.id


@pytest.mark.django_db
def test_verbose_name_francais():
    meta = EventLog._meta

    assert meta.verbose_name == "historique des évenements"
    assert meta.verbose_name_plural == "historique des évenements"

    # Vérifie les verbose_name des champs
    id_field = meta.get_field("id")
    assert id_field.verbose_name == "identifiant"

    created_at_field = meta.get_field("created_at")
    assert created_at_field.verbose_name == "date de création"

    level_field = meta.get_field("level")
    assert level_field.verbose_name == "niveau de log"

    msg_field = meta.get_field("msg")
    assert msg_field.verbose_name == "message"

    payload_field = meta.get_field("payload")
    assert payload_field.verbose_name == "contenu supplémentaire (JSON)"


@pytest.mark.django_db
def test_indexes_existent():
    meta = EventLog._meta
    indexes = meta.indexes

    # Vérifie qu'il y a bien 2 index
    assert len(indexes) == 2

    # Récupère les noms de champs indexés
    indexed_fields = []
    for index in indexes:
        indexed_fields.extend(index.fields)

    assert "level" in indexed_fields
    assert "created_at" in indexed_fields


@pytest.mark.django_db
@pytest.mark.slow
def test_performance_insertion_bulk():
    events = [
        EventLog(
            level=logging.INFO,
            msg=f"Event {i}",
            payload={"index": i},
        )
        for i in range(100)
    ]

    with CaptureQueriesContext(connection) as context:
        EventLog.objects.bulk_create(events)

    # bulk_create devrait faire une seule requête
    assert len(context.captured_queries) == 1

    # Vérifie que tous les événements ont été créés
    assert EventLog.objects.count() == 100


@pytest.mark.django_db
def test_payload_avec_caracteres_speciaux():
    payload = {
        "message": "Événement spécial avec accents: é, è, à, ç",
        "emoji": "🚀 🎉 ✨",
        "symbols": "< > & ' \" \\ / ",
        "unicode": "日本語 中文 한글",
    }

    event = EventLog.objects.create(
        level=logging.INFO,
        msg="Test caractères spéciaux",
        payload=payload,
    )

    event_db = EventLog.objects.get(id=event.id)
    assert event_db.payload == payload
    assert event_db.payload["emoji"] == "🚀 🎉 ✨"
