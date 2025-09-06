from django.contrib.auth import get_user_model
from rest_framework import status
from scheduler.models import TaskCategory, Task
from model_bakery import baker
import pytest

User = get_user_model()


@pytest.mark.django_db
class TestCreateCategory:

    def test_unauthenticated_category_creation_returns_401(self, api_client):
        response = api_client.post(
            "/api/schedule/categories/", {"title": "Title for test"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_authenticated_category_creation_returns_201(
        self, authentication, api_client
    ):
        title = "Title for test"
        user = authentication()

        response = api_client.post("/api/schedule/categories/", {"title": title})

        assert response.status_code == status.HTTP_201_CREATED
        assert "id" in response.data and "title" in response.data
        assert TaskCategory.objects.filter(title=title, user=user).exists()

    def test_if_category_for_user_exists_returns_400(self, authentication, api_client):
        title = "Sample"
        user = authentication()
        TaskCategory.objects.create(title=title, user=user)

        response = api_client.post("/api/schedule/categories/", {"title": title})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.parametrize("title", ["", "a" * 151])
    def test_create_invalid_data_returns_400(self, authentication, api_client, title):
        authentication()

        response = api_client.post("/api/schedule/categories/", {"title": title})

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestRetriveCategory:
    def test_if_authenticated_user_is_owner_returns_200(
        self, authentication, api_client
    ):
        user = authentication()
        category = baker.make(TaskCategory, user=user)

        response = api_client.get(f"/api/schedule/categories/{category.id}/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data == {
            "id": category.id,
            "title": category.title,
            "task_count": 0,
        }

    def test_if_category_not_found(self, authentication, api_client):
        authentication()

        response = api_client.get(f"/api/schedule/categories/{9999}/")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_if_authenticated_user_is_not_owner_returns_404(
        seld, authentication, api_client
    ):
        owner_user = baker.make(User)
        category = baker.make(TaskCategory, user=owner_user)
        authentication()

        response = api_client.get(f"/api/schedule/categories/{category.id}/")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_categories_task_count(self, authentication, api_client):
        user = authentication()
        category = baker.make(TaskCategory, user=user)
        baker.make(Task, category=category, user=user, _quantity=5)

        response = api_client.get(f"/api/schedule/categories/{category.id}/")

        assert response.status_code == status.HTTP_200_OK
        assert "task_count" in response.data
        assert response.data["task_count"] == 5


@pytest.mark.django_db
class TestListCategories:
    def test_authenticated_user_gets_owned_categories(self, authentication, api_client):
        user = authentication()
        categories = baker.make(TaskCategory, user=user, _quantity=5)
        tasks_id = [task.id for task in categories]
        baker.make(TaskCategory, _quantity=10)  # anonymous tasks

        response = api_client.get("/api/schedule/categories/")
        fetched_tasks_id = [task["id"] for task in response.data]

        assert response.status_code == status.HTTP_200_OK
        assert set(tasks_id) == set(fetched_tasks_id)


@pytest.mark.django_db
class TestEditCategories:
    def test_unauthenticated_editing_categories_returns_401(self, api_client):
        category = baker.make(TaskCategory)

        response = api_client.put(
            f"/api/schedule/categories/{category.id}/", {"title": "new_title"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_authenticated_editing_categories_returns_200(
        self, authentication, api_client
    ):
        user = authentication()
        category = baker.make(TaskCategory, user=user)
        new_title = "New_title"

        response = api_client.put(
            f"/api/schedule/categories/{category.id}/", {"title": new_title}
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == new_title
        assert TaskCategory.objects.filter(pk=category.pk).first().title == new_title

    def test_if_user_editing_another_task_returns_404(self, authentication, api_client):
        user = baker.make(User)
        category = baker.make(TaskCategory, user=user)

        authentication()
        response = api_client.put(
            f"/api/schedule/categories/{category.id}/", {"title": "new_title"}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
