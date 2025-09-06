from datetime import date, timedelta
from django.shortcuts import get_object_or_404
from django.db.models.aggregates import Count
from django.db.models import Prefetch, Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.generics import CreateAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status
from .filters import TaskFilter
from .models import Tag, Task, TaskCategory, SubTask, TaggedItem
from .permissions import IsAuthenticatedAndOwner
from .serializers import (
    TaskCategorySerializer,
    TaskSerializer,
    TaskCreateSerializer,
    TaskUpdateSerializer,
    SubTaskSerializer,
    TagSerializer,
    TaggedItemSerializer,
    FullTaskCreateSerializer,
    OptimizedTaskUpdateSerializer,
)


class TaskCategoryViewSet(ModelViewSet):
    serializer_class = TaskCategorySerializer
    permission_classes = [IsAuthenticatedAndOwner]

    def get_queryset(self):
        user = self.request.user
        return TaskCategory.objects.annotate(task_count=Count("task")).filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TaskViewSet(ModelViewSet):
    permission_classes = [IsAuthenticatedAndOwner]
    filter_backends = [DjangoFilterBackend]
    filterset_class = TaskFilter

    def get_queryset(self):
        user = self.request.user
        queryset = (
            Task.objects.filter(user=user)
            .select_related("category")
            .prefetch_related(
                "subTasks",
                Prefetch(
                    "tagged_items",
                    queryset=TaggedItem.objects.select_related("tag").filter(
                        tag__user=user
                    ),
                    to_attr="prefetched_tagged_items",
                ),
            )
        )

        date_param = self.request.query_params.get("scheduled_date")
        if self.action == "list" and not date_param:
            # this will return the tasks for today, tommorow(for upcomming tasks),
            # And tasks whose deadlines are still ongoing.
            today = date.today()
            queryset = queryset.filter(
                Q(scheduled_date__in=[today, (today + timedelta(days=1))])
                | Q(
                    scheduled_date__lt=today,
                    dead_line__gte=today,
                    is_completed__exact=False,
                )
            )

        return queryset

    def get_serializer_class(self):
        if self.request.method == "POST":
            return TaskCreateSerializer
        if self.request.method in ("PUT", "PATCH"):
            return TaskUpdateSerializer
        return TaskSerializer

    def perform_create(self, serializer):
        return serializer.save(user=self.request.user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


class SubTaskViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = SubTaskSerializer

    def get_queryset(self):
        task_id = self.kwargs["task_pk"]

        task = get_object_or_404(Task, pk=task_id, user=self.request.user)

        return SubTask.objects.filter(parent_task=task)

    def get_serializer_context(self):
        return {"task_pk": self.kwargs["task_pk"]}


class TagViewSet(ModelViewSet):
    permission_classes = [IsAuthenticatedAndOwner]
    serializer_class = TagSerializer

    def get_queryset(self):
        user = self.request.user
        return Tag.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TaggedItemViewSet(ModelViewSet):
    serializer_class = TaggedItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        tag_id = self.kwargs["tag_pk"]
        return TaggedItem.objects.filter(tag__id=tag_id, tag__user=self.request.user)

    def perform_create(self, serializer):
        tag = get_object_or_404(Tag, id=self.kwargs["tag_pk"], user=self.request.user)
        serializer.save(tag=tag)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


class FullTaskCreateView(CreateAPIView):
    queryset = Task.objects.all()
    serializer_class = FullTaskCreateSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        task = serializer.instance
        response = TaskSerializer(task)

        return Response(response.data, status=status.HTTP_201_CREATED)


# clude
class OptimizedTaskUpdateView(UpdateAPIView):
    """ویو بهینه برای آپدیت تسک‌ها"""

    serializer_class = OptimizedTaskUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Task.objects.filter(user=self.request.user)
            .select_related("category")
            .prefetch_related("subTasks", "tagged_items__tag")
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updated_instance = serializer.save()

        response_serializer = TaskSerializer(updated_instance)

        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)
