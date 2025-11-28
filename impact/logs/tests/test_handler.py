import logging

import pytest

from logs import event_logger
from logs.event import EventLogHandler
from logs.models import EventLog


@pytest.mark.django_db
@pytest.mark.parametrize(
    "log_level,log_method,level_name",
    [
        (logging.INFO, "info", "INFO"),
        (logging.WARNING, "warning", "WARNING"),
        (logging.ERROR, "error", "ERROR"),
        (logging.CRITICAL, "critical", "CRITICAL"),
    ],
)
def test_handler_emit_log_niveaux_standards(log_level, log_method, level_name):
    log_function = getattr(event_logger, log_method)
    log_function(f"Test message {level_name}")

    events = EventLog.objects.all()
    assert events.count() == 1

    event = events.first()
    assert event.level == log_level
    assert event.msg == f"Test message {level_name}"
    assert event.payload == {}


@pytest.mark.django_db
def test_handler_emit_log_debug_non_persiste():
    event_logger.debug("Test message DEBUG")

    # DEBUG est en dessous du niveau INFO configuré, donc pas persisté
    assert EventLog.objects.count() == 0


@pytest.mark.django_db
def test_handler_avec_payload_dict():
    payload = {
        "user_id": 123,
        "action": "login",
        "ip": "192.168.1.1",
    }

    event_logger.info("User action", payload)

    event = EventLog.objects.first()
    assert event.msg == "User action"
    assert event.payload == payload
    assert event.payload["user_id"] == 123
    assert event.payload["action"] == "login"


@pytest.mark.django_db
def test_handler_avec_payload_complexe():
    payload = {
        "user": {"id": 42, "name": "Alice"},
        "actions": ["view", "edit", "save"],
        "metadata": {"browser": "Firefox", "os": "Linux"},
    }

    event_logger.info("Complex action", payload)

    event = EventLog.objects.first()
    assert event.payload["user"]["name"] == "Alice"
    assert len(event.payload["actions"]) == 3
    assert event.payload["metadata"]["browser"] == "Firefox"


@pytest.mark.django_db
def test_handler_sans_payload():
    event_logger.info("Simple message")

    event = EventLog.objects.first()
    assert event.msg == "Simple message"
    assert event.payload == {}


@pytest.mark.django_db
def test_handler_avec_args_non_dict():
    # Les args normaux de logging (non-dict) ne doivent pas planter
    event_logger.info("Message with args %s %d", "test", 123)

    event = EventLog.objects.first()
    # Le message est formaté avec les args
    assert "Message with args" in event.msg
    # Mais le payload reste vide car args n'est pas un dict
    assert event.payload == {}


@pytest.mark.django_db
def test_handler_multiples_logs():
    event_logger.info("Premier log")
    event_logger.warning("Deuxième log")
    event_logger.error("Troisième log")

    assert EventLog.objects.count() == 3

    events = EventLog.objects.all().order_by("created_at")
    assert events[0].msg == "Premier log"
    assert events[1].msg == "Deuxième log"
    assert events[2].msg == "Troisième log"


@pytest.mark.django_db
def test_handler_log_avec_caracteres_speciaux():
    payload = {
        "message": "Événement avec accents: é, è, à",
        "emoji": "🚀 ✨",
    }

    event_logger.info("Message spécial: é, è, ç", payload)

    event = EventLog.objects.first()
    assert "é, è, ç" in event.msg
    assert event.payload["emoji"] == "🚀 ✨"


@pytest.mark.django_db
def test_handler_instance_directe():
    handler = EventLogHandler()

    # Crée un LogRecord manuellement
    record = logging.LogRecord(
        name="test",
        level=logging.WARNING,
        pathname="test.py",
        lineno=1,
        msg="Direct handler test",
        args={},
        exc_info=None,
    )

    handler.emit(record)

    event = EventLog.objects.first()
    assert event.level == logging.WARNING
    assert event.msg == "Direct handler test"


@pytest.mark.django_db
def test_handler_avec_payload_vide_dict():
    # Note: passer un dict vide comme args est interprété par Python logging
    # comme un formatage de string, donc on teste plutôt un dict avec au moins une clé
    event_logger.info("Message sans données", {"empty": True})

    event = EventLog.objects.first()
    assert event.msg == "Message sans données"
    assert event.payload == {"empty": True}


@pytest.mark.django_db
def test_handler_log_record_avec_payload_dict():
    handler = EventLogHandler()

    payload = {"user": "alice", "action": "delete"}
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="User action logged",
        args=payload,
        exc_info=None,
    )

    handler.emit(record)

    event = EventLog.objects.first()
    assert event.msg == "User action logged"
    assert event.payload == payload


@pytest.mark.django_db
def test_handler_log_record_avec_args_tuple():
    handler = EventLogHandler()

    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test with tuple args",
        args=("arg1", "arg2"),
        exc_info=None,
    )

    handler.emit(record)

    event = EventLog.objects.first()
    assert event.payload == {}


@pytest.mark.django_db
def test_handler_log_message_vide():
    event_logger.info("")

    event = EventLog.objects.first()
    assert event.msg == ""
    assert event.level == logging.INFO


@pytest.mark.django_db
def test_handler_log_message_tres_long():
    long_message = "A" * 5000

    event_logger.info(long_message)

    event = EventLog.objects.first()
    assert event.msg == long_message
    assert len(event.msg) == 5000


@pytest.mark.django_db
@pytest.mark.slow
def test_handler_performance_multiples_logs():
    for i in range(50):
        event_logger.info(f"Log number {i}", {"index": i})

    assert EventLog.objects.count() == 50

    # Vérifie quelques logs au hasard
    first_log = EventLog.objects.filter(payload__index=0).first()
    assert first_log is not None
    assert first_log.payload["index"] == 0

    last_log = EventLog.objects.filter(payload__index=49).first()
    assert last_log is not None
    assert last_log.payload["index"] == 49


@pytest.mark.django_db
def test_handler_configuration_logger():
    # Vérifie que le logger event_logger existe
    assert event_logger.name == "logs.event"

    # Vérifie que le handler EventLogHandler est attaché
    handlers = [h for h in event_logger.handlers if isinstance(h, EventLogHandler)]
    assert len(handlers) > 0


@pytest.mark.django_db
def test_handler_niveau_info_par_defaut():
    # DEBUG ne devrait pas être loggé
    event_logger.debug("Debug message")
    assert EventLog.objects.count() == 0

    # INFO devrait être loggé
    event_logger.info("Info message")
    assert EventLog.objects.count() == 1
