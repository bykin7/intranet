from django import forms
from django.contrib.auth.models import User

from .models import Task
from feed.permissions import get_visible_users_for_user


class UserFullNameChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        try:
            full_name = obj.profile.full_name
            position = obj.profile.get_position_display()
        except Exception:
            full_name = ""
            position = ""

        if not full_name:
            full_name = "Без ФИО"

        if position:
            return f"{full_name} — {position}"

        return full_name


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean

        if isinstance(data, (list, tuple)):
            result = [single_file_clean(file, initial) for file in data]
        else:
            result = single_file_clean(data, initial)

        return result


class TaskForm(forms.ModelForm):
    assignee = UserFullNameChoiceField(
        label="Исполнитель",
        queryset=User.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    images = MultipleFileField(
        label="Фотографии",
        required=False,
        widget=MultipleFileInput(
            attrs={
                "class": "form-control",
                "accept": "image/*",
                "multiple": True,
            }
        ),
        help_text="Можно прикрепить несколько фотографий к задаче.",
    )

    class Meta:
        model = Task
        fields = [
            "assignee",
            "title",
            "description",
            "priority",
            "due_date",
            "images",
        ]

        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Коротко: что сделать",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": "Подробности задачи",
                }
            ),
            "priority": forms.Select(attrs={"class": "form-select"}),
            "due_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        if user:
            self.fields["assignee"].queryset = (
                get_visible_users_for_user(user)
                .exclude(id=user.id)
                .order_by("profile__full_name", "username")
            )
        else:
            self.fields["assignee"].queryset = User.objects.none()