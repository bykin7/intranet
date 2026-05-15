from django import forms
from django.contrib.auth.models import User

from .models import GroupChat
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


class NewPrivateChatForm(forms.Form):
    user = UserFullNameChoiceField(
        label="Сотрудник",
        queryset=User.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"})
    )

    def __init__(self, *args, current_user=None, **kwargs):
        super().__init__(*args, **kwargs)

        if current_user:
            self.fields["user"].queryset = (
                get_visible_users_for_user(current_user)
                .exclude(id=current_user.id)
                .order_by("profile__full_name", "username")
            )


class GroupChatForm(forms.ModelForm):
    class Meta:
        model = GroupChat
        fields = ["name", "description"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }


class AddGroupChatMemberForm(forms.Form):
    user = UserFullNameChoiceField(
        label="Сотрудник",
        queryset=User.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"})
    )

    def __init__(self, *args, current_user=None, **kwargs):
        super().__init__(*args, **kwargs)

        if current_user:
            self.fields["user"].queryset = (
                get_visible_users_for_user(current_user)
                .exclude(id=current_user.id)
                .order_by("profile__full_name", "username")
            )