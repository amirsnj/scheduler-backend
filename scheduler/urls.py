from django.urls import path, include
from rest_framework_nested import routers
from . import views


router = routers.DefaultRouter()

router.register("categories", views.TaskCategoryViewSet, basename="category")
router.register("tasks", views.TaskViewSet, basename="task")
router.register("tags", views.TagViewSet, basename="tag")

tasks_router = routers.NestedDefaultRouter(router, "tasks", lookup="task")
tasks_router.register("sub-tasks", views.SubTaskViewSet, basename="task-subTask")

taggedItems_router = routers.NestedDefaultRouter(router, "tags", lookup="tag")
taggedItems_router.register("tagged-items", views.TaggedItemViewSet, basename="tag-taggedItems")

urlpatterns = [
    path('tasks/full-create/', views.FullTaskCreateView.as_view()),
    path('tasks/<int:pk>/update/', views.OptimizedTaskUpdateView.as_view()),
    path('', include(router.urls)),
    path('', include(tasks_router.urls)),
    path('', include(taggedItems_router.urls))
]