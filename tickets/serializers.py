from rest_framework import serializers

from .models import Category, Ticket


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name")


class TicketSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(
        source="category.name",
        read_only=True,
    )

    status_label = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )

    class Meta:
        model = Ticket

        fields = (
            "id",
            "title",
            "description",
            "category",
            "category_name",
            "status",
            "status_label",
            "created_at",
        )

        read_only_fields = (
            "id",
            "created_at",
        )

        extra_kwargs = {
            "title": {
                "error_messages": {
                    "blank": "Введите название заявки.",
                    "required": "Введите название заявки.",
                    "max_length": (
                        "Название должно содержать "
                        "не более 200 символов."
                    ),
                },
            },
            "category": {
                "error_messages": {
                    "required": "Выберите категорию.",
                    "null": "Выберите категорию.",
                    "does_not_exist": "Выбранная категория не существует.",
                    "incorrect_type": "Некорректная категория.",
                },
            },
            "status": {
                "error_messages": {
                    "invalid_choice": "Недопустимый статус.",
                },
            },
        }

    def validate_title(self, value):
        value = value.strip()

        if len(value) < 5:
            raise serializers.ValidationError(
                "Название должно содержать не менее 5 символов."
            )

        return value

    def validate(self, attrs):
        if self.instance is None:
            status = attrs.get("status", Ticket.Status.NEW)

            if status != Ticket.Status.NEW:
                raise serializers.ValidationError({
                    "status": (
                        "Новая заявка должна иметь статус «Новая»."
                    ),
                })

            return attrs

        old_status = self.instance.status
        new_status = attrs.get("status", old_status)

        allowed_transitions = {
            Ticket.Status.NEW: {Ticket.Status.PROGRESS},
            Ticket.Status.PROGRESS: {Ticket.Status.DONE},
            Ticket.Status.DONE: set(),
        }

        if (
            new_status != old_status
            and new_status not in allowed_transitions[old_status]
        ):
            raise serializers.ValidationError({
                "status": (
                    "Недопустимый переход. Разрешена последовательность: "
                    "«Новая» → «В работе» → «Выполнена»."
                ),
            })

        return attrs