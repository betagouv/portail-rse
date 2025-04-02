import os

# attention: DJANGO_SETTINGS_MODULE est toujours initialisé
if os.getenv("DJANGO_SETTINGS_MODULE") == __name__:
    # Configuration par défaut : production
    from .prod import *  # noqa
