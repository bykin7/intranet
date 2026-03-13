from django import forms
from django.contrib.auth.models import User
from .models import GroupChat


class NewPrivateChatForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=User.objects.all().order_by("username"),
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Сотрудник"
    )


class GroupChatForm(forms.ModelForm):
    class Meta:
        model = GroupChat
        fields = ["name", "description"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Название группы"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "Описание группы"}),
        }


class AddGroupChatMemberForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=User.objects.all().order_by("username"),
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Сотрудник"
    )