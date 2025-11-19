import logging

# Raccourci et side effect
event_logger = logging.getLogger("logs.event")

from .decorators import log_path as log_path  # noqa
