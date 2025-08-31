from rest_framework import status
from scheduler.models import TaskCategory
import pytest



@pytest.mark.django_db
class TestCreateCategory:

    def test_unauthenticated_category_creation_returns_401(self, api_client):
        response = api_client.post("/api/schedule/categories/", {"title": "Title for test"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


    def test_authenticated_category_creation_returns_201(self, authentication, api_client):
        title = "Title for test"
        user = authentication(username="user_test", email="test@example.com", password="password123")

        response = api_client.post("/api/schedule/categories/", {"title": title})
                                                            
        assert response.status_code == status.HTTP_201_CREATED
        assert "id" in response.data and "title" in response.data
        assert TaskCategory.objects.filter(title=title, user=user).exists()


    def test_if_category_for_user_exists_returns_400(self, authentication, api_client):
        title = "Sample"
        user = authentication(username="user_test", email="test@example.com", password="password123")
        TaskCategory.objects.create(title=title, user=user)

        response = api_client.post("/api/schedule/categories/", {"title": title})

        assert response.status_code == status.HTTP_400_BAD_REQUEST


    @pytest.mark.parametrize("title", ["", "a" * 151])
    def test_create_invalid_data_returns_400(self, authentication, api_client, title):
        authentication(username="user_test", email="test@example.com", password="password123")

        response = api_client.post("/api/schedule/categories/", {"title": title})

        assert response.status_code == status.HTTP_400_BAD_REQUEST