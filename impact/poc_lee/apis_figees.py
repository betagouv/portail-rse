from contextlib import contextmanager
from contextlib import ExitStack
from unittest.mock import patch


@contextmanager
def apis_externes_figees():
    with ExitStack() as pile:
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
