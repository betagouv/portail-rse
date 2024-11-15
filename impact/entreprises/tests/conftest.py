from datetime import datetime

import pytest
from django.utils import timezone


@pytest.fixture
def date_requalification():
    # Modifie la date buttoir de requalification pour compatibilité des tests
    import entreprises.models as models  # noqa

    orig_date, models.DATE_REQUALIFICATION = (
        models.DATE_REQUALIFICATION,
        timezone.make_aware(datetime.strptime("2021-11-15", "%Y-%m-%d")),
    )
    yield
    models.DATE_REQUALIFICATION = orig_date
