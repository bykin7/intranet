from django import forms

from .models import GroupChat
from feed.access import get_visible_users_for_user


class UserFullNameChoiceField(forms.ModelChoiceField):
    """Показывает ФИО сотрудника вместо его логина."""

    def label_from_instance(self, user):
        try:
            full_name = (user.profile.full_name or "").strip()
            position = user.profile.get_position_display()
        except Exception:
            full_name = ""
            position = ""

        if not full_name:
            full_name = user.username

        if position:
            return f"{full_name} — {position}"

        return full_name


class NewPrivateChatForm(forms.Form):
    user = UserFullNameChoiceField(
        queryset=None,
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Сотрудник",
    )

    def __init__(self, *args, current_user=None, **kwargs):
        super().__init__(*args, **kwargs)

        if current_user:
            self.fields["user"].queryset = get_visible_users_for_user(
                current_user,
                include_self=False,
            )
        else:
            self.fields["user"].queryset = get_visible_users_for_user(None)


class GroupChatForm(forms.ModelForm):
    class Meta:
        model = GroupChat
        fields = ["name", "description"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Название группы",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Описание группы",
                }
            ),
        }


class AddGroupChatMemberForm(forms.Form):
    user = UserFullNameChoiceField(
        queryset=None,
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Сотрудник",
    )

    def __init__(self, *args, current_user=None, **kwargs):
        super().__init__(*args, **kwargs)

        if current_user:
            self.fields["user"].queryset = get_visible_users_for_user(
                current_user,
                include_self=False,
            )
        else:
            self.fields["user"].queryset = get_visible_users_for_user(None)
