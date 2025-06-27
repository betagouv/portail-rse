import logging


class EventLogHandler(logging.Handler):
    def emit(self, record: logging.LogRecord):
        # voir : https://docs.python.org/3/library/logging.html#logrecord-attributes
        payload = {}
        if record.args and isinstance(record.args, dict):
            payload |= record.args

        # les logs sont définis avant le démarrage des apps django
        # l'import ne doit pas être fait en entête...
        from .models import EventLog

        EventLog(level=record.levelno, msg=record.msg, payload=payload).save()
