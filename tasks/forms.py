from django import forms
from django.contrib.auth.models import User
from .models import Task


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["assignee", "title", "description", "priority", "due_date"]
        widgets = {
            "assignee": forms.Select(attrs={"class": "form-select"}),
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Коротко: что сделать"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 5, "placeholder": "Подробности (необязательно)"}),
            "priority": forms.Select(attrs={"class": "form-select"}),
            "due_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assignee"].queryset = User.objects.order_by("username")