from django.db import models
from django.conf import settings
from scheduler.validators import validate_date_not_past
from datetime import date


class TaskCategory(models.Model):
    title = models.CharField(max_length=150)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="taskCategories",
    )

    class Meta:
        unique_together = ["title", "user"]

    def __str__(self):
        return self.title


class Task(models.Model):
    PRIORITY_LEVEL_LOW = "L"
    PRIORITY_LEVEL_MEDIUM = "M"
    PRIORITY_LEVEL_HIGH = "H"

    PRIORITY_LEVEL_CHOICES = [
        (PRIORITY_LEVEL_LOW, "Low"),
        (PRIORITY_LEVEL_MEDIUM, "Medium"),
        (PRIORITY_LEVEL_HIGH, "High"),
    ]

    title = models.CharField(max_length=150)
    description = models.TextField(max_length=200, default="", blank=True)
    category = models.ForeignKey(TaskCategory, on_delete=models.SET_NULL, null=True)
    priority_level = models.CharField(
        max_length=1, choices=PRIORITY_LEVEL_CHOICES, default=PRIORITY_LEVEL_MEDIUM
    )
    scheduled_date = models.DateField(default=date.today)
    dead_line = models.DateField(null=True, validators=[validate_date_not_past])
    is_completed = models.BooleanField(default=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tasks"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["user", "scheduled_date"])]

    def __str__(self):
        return self.title


class SubTask(models.Model):
    title = models.CharField(max_length=150)
    is_completed = models.BooleanField(default=False)
    parent_task = models.ForeignKey(
        Task, on_delete=models.CASCADE, related_name="subTasks"
    )


class Tag(models.Model):
    title = models.CharField(max_length=40)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tags"
    )

    class Meta:
        unique_together = ["title", "user"]

    def __str__(self):
        return self.title


class TaggedItem(models.Model):
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    task = models.ForeignKey(
        Task, on_delete=models.CASCADE, related_name="tagged_items"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["tag", "task"]
