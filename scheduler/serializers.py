from django.db import transaction, IntegrityError
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from scheduler.models import Tag, TaskCategory, Task, SubTask, TaggedItem


class TaskCategorySerializer(serializers.ModelSerializer):
    task_count = serializers.SerializerMethodField()

    def get_task_count(self, obj):
        return getattr(obj, "task_count", 0)

    def validate_title(self, value: str):
        return value.strip().capitalize()

    class Meta:
        model = TaskCategory
        fields = ["id", "title", "task_count"]

    def create(self, validated_data):
        try:
            category = TaskCategory.objects.create(**validated_data)
            return category
        except IntegrityError:
            raise ValidationError({"detail": "The Category is already exists."})


class SubTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubTask
        fields = ["id", "title", "is_completed"]

    def create(self, validated_data):
        parent_id = self.context["task_pk"]
        return SubTask.objects.create(**validated_data, parent_task_id=parent_id)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "title"]

    def validate_title(self, value: str):
        return value.strip().capitalize()

    def create(self, validated_data):
        try:
            tag = Tag.objects.create(**validated_data)
            return tag
        except IntegrityError:
            raise ValidationError({"detail": "The Tag is already exists."})


class TaskSerializer(serializers.ModelSerializer):
    subTasks = SubTaskSerializer(many=True)
    tags = serializers.SerializerMethodField()

    def get_tags(self, obj):
        if hasattr(obj, "prefetched_tagged_items"):
            tagged_items = obj.prefetched_tagged_items
        else:
            tagged_items = obj.tagged_items.select_related("tag").all()

        tags = [item.tag for item in tagged_items]
        return TagSerializer(tags, many=True).data

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "category",
            "priority_level",
            "scheduled_date",
            "dead_line",
            "start_time",
            "end_time",
            "is_completed",
            "subTasks",
            "updated_at",
            "tags",
        ]


class TaskCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            "title",
            "description",
            "category",
            "priority_level",
            "scheduled_date",
            "start_time",
            "end_time",
            "dead_line"
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        request = self.context.get("request")

        if request and hasattr(request, "user"):
            self.fields["category"].queryset = TaskCategory.objects.filter(
                user=request.user
            )

    def validate_category(self, value):
        if value is None:
            return value

        request = self.context.get("request")
        if (
            request
            and not TaskCategory.objects.filter(title=value, user=request.user).exists()
        ):
            raise serializers.ValidationError({"detail": "The task category not found"})
        return value

    def validate(self, attrs):
        scheduled_date = attrs.get("scheduled_date")
        dead_line = attrs.get("dead_line")
        start_time = attrs.get("start_time")
        end_time = attrs.get("end_time")

        if scheduled_date and dead_line and scheduled_date > dead_line:
            raise serializers.ValidationError(
                {"detail": "Schedule date cannot be grater than deadline date."}
            )
        
        if start_time and end_time and start_time > end_time:
            if dead_line and not scheduled_date < dead_line:
                raise serializers.ValidationError(
                    {"detail": "End time cannot be less than start time."}
                )


        return attrs


class TaskUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            "title",
            "description",
            "category",
            "priority_level",
            "scheduled_date",
            "dead_line",
            "start_time",
            "end_time",
            "is_completed",
        ]

    def validate_category(self, value):
        if value is None:
            return value

        request = self.context.get("request")
        if (
            request
            and not TaskCategory.objects.filter(title=value, user=request.user).exists()
        ):
            raise serializers.ValidationError({"detail": "The task category not found"})
        return value

    def validate(self, attrs):
        scheduled_date = attrs.get("scheduled_date")
        dead_line = attrs.get("dead_line")
        start_time = attrs.get("start_time")
        end_time = attrs.get("end_time")

        if scheduled_date and dead_line and scheduled_date > dead_line:
            raise serializers.ValidationError(
                {"detail": "Schedule date cannot be grater than deadline date."}
            )
        
        if start_time and end_time and start_time > end_time:
            if dead_line and not scheduled_date < dead_line:
                raise serializers.ValidationError(
                    {"detail": "End time cannot be less than start time."}
                )

        return attrs


class TaggedItemSerializer(serializers.ModelSerializer):
    task_id = serializers.PrimaryKeyRelatedField(
        queryset=Task.objects.none(), source="task"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        request = self.context.get("request")
        if request and hasattr(request, "user"):
            self.fields["task_id"].queryset = Task.objects.filter(user=request.user)

    class Meta:
        model = TaggedItem
        fields = ["id", "task_id", "created_at"]
        read_only_fields = ["id", "created_at"]

    def create(self, validated_data):
        task = validated_data.get("task")
        tag = validated_data.get("tag")
        if task and TaggedItem.objects.filter(tag=tag, task=task).exists():
            raise ValidationError(
                {
                    "detail": "The current task has already tagged with this selected tag."
                }
            )

        return super().create(validated_data)


class FullTaskCreateSerializer(serializers.ModelSerializer):
    tags = serializers.ListField(child=serializers.IntegerField(), required=False)
    subTasks = SubTaskSerializer(many=True, required=False)

    class Meta:
        model = Task
        fields = [
            "title",
            "description",
            "category",
            "priority_level",
            "scheduled_date",
            "start_time",
            "end_time",
            "dead_line",
            "tags",
            "subTasks",
        ]

    def create(self, validated_data):
        tags = validated_data.pop("tags", [])
        sub_tasks = validated_data.pop("subTasks", [])

        request = self.context.get("request")
        user = request.user

        with transaction.atomic():
            task = Task.objects.create(user=user, **validated_data)

            tagged_items = [TaggedItem(tag_id=tag_id, task=task) for tag_id in tags]

            sub_tasks = [
                SubTask(parent_task=task, **sub_task) for sub_task in sub_tasks
            ]

            TaggedItem.objects.bulk_create(tagged_items)
            SubTask.objects.bulk_create(sub_tasks)

        return task


class OptimizedTaskUpdateSerializer(serializers.ModelSerializer):
    tags = serializers.ListField(
        child=serializers.IntegerField(), required=False, allow_empty=True
    )
    subTasks = SubTaskSerializer(many=True, required=False, allow_empty=True)

    class Meta:
        model = Task
        fields = [
            "title",
            "description",
            "category",
            "priority_level",
            "scheduled_date",
            "dead_line",
            "start_time",
            "end_time",
            "is_completed",
            "tags",
            "subTasks",
        ]

    def update(self, instance, validated_data):
        tags = validated_data.pop("tags", None)
        sub_tasks = validated_data.pop("subTasks", None)

        with transaction.atomic():

            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            if tags is not None:
                self._update_tags_optimized(instance, tags)

            if sub_tasks is not None:
                self._update_subtasks_optimized(instance, sub_tasks)

        instance.refresh_from_db()
        return instance

    def _update_tags_optimized(self, task, new_tags):
        current_tags = set(
            TaggedItem.objects.filter(task=task).values_list("tag_id", flat=True)
        )
        new_tags_set = set(new_tags)

        tags_to_remove = current_tags - new_tags_set
        if tags_to_remove:
            TaggedItem.objects.filter(task=task, tag_id__in=tags_to_remove).delete()

        tags_to_add = new_tags_set - current_tags
        if tags_to_add:
            tagged_items = [
                TaggedItem(tag_id=tag_id, task=task) for tag_id in tags_to_add
            ]
            TaggedItem.objects.bulk_create(tagged_items)

    def _update_subtasks_optimized(self, task, new_subtasks):
        current_subtasks = {
            st.id: st for st in SubTask.objects.filter(parent_task=task)
        }

        subtasks_to_update = []
        subtasks_to_create = []
        updated_ids = set()

        for subtask_data in new_subtasks:
            subtask_id = subtask_data.get("id")

            if subtask_id and subtask_id in current_subtasks:
                subtask_instance = current_subtasks[subtask_id]
                subtask_instance.title = subtask_data.get(
                    "title", subtask_instance.title
                )
                subtask_instance.is_completed = subtask_data.get(
                    "is_completed", subtask_instance.is_completed
                )
                subtasks_to_update.append(subtask_instance)
                updated_ids.add(subtask_id)
            else:
                subtasks_to_create.append(
                    SubTask(
                        parent_task=task,
                        title=subtask_data.get("title", ""),
                        is_completed=subtask_data.get("is_completed", False),
                    )
                )

        subtasks_to_delete = set(current_subtasks.keys()) - updated_ids
        if subtasks_to_delete:
            SubTask.objects.filter(id__in=subtasks_to_delete).delete()

        if subtasks_to_update:
            SubTask.objects.bulk_update(subtasks_to_update, ["title", "is_completed"])

        if subtasks_to_create:
            SubTask.objects.bulk_create(subtasks_to_create)
