from django_filters import FilterSet
from .models import Task


class TaskFilter(FilterSet):
    class Meta:
        model = Task
        fields = {"category": ["exact"], "scheduled_date": ["exact"]}
