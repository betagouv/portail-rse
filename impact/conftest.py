import pytest


@pytest.fixture
def alice(django_user_model):
    alice = django_user_model.objects.create(email="alice@impact.test")
    return alice