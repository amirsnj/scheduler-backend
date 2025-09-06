from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
import pytest

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authentication(api_client):
    def inner_function(is_staff=False):
        user = User.objects.create_user(
            username="user_test",
            email="user@example.com",
            password="password123",
            is_staff=is_staff,
        )
        api_client.force_authenticate(user=user)
        return user

    return inner_function
