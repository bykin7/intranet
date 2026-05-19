from django import forms
from .models import GroupChat
from feed.access import get_visible_users_for_user


class NewPrivateChatForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=None,
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Сотрудник"
    )

    def __init__(self, *args, current_user=None, **kwargs):
        super().__init__(*args, **kwargs)

        if current_user:
            self.fields["user"].queryset = get_visible_users_for_user(
                current_user,
                include_self=False
            )
        else:
            self.fields["user"].queryset = get_visible_users_for_user(None)


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
        queryset=None,
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Сотрудник"
    )

    def __init__(self, *args, current_user=None, **kwargs):
        super().__init__(*args, **kwargs)

        if current_user:
            self.fields["user"].queryset = get_visible_users_for_user(
                current_user,
                include_self=False
            )
        else:
            self.fields["user"].queryset = get_visible_users_for_user(None)