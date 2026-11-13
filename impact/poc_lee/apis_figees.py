import threading
from contextlib import contextmanager
from contextlib import ExitStack
from unittest.mock import patch

# Le patch est global au process : le verrou empêche deux requêtes simultanées
# de se restaurer mutuellement un mock à la place de la vraie fonction.
_verrou = threading.Lock()


@contextmanager
def apis_externes_figees():
    with _verrou, ExitStack() as pile:
        pile.enter_context(
            patch("api.egapro.is_index_egapro_published", return_value=False)
        )
        pile.enter_context(
            patch(
                "api.egapro.indicateurs_bdese",
                return_value={
                    "nombre_femmes_plus_hautes_remunerations": None,
                    "objectifs_progression": None,
                },
            )
        )
        pile.enter_context(patch("api.bges.last_reporting_year", return_value=None))
        yield
