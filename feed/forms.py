from django import forms
from django.contrib.auth.models import User
from .models import Post, Profile


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["title", "body", "is_pinned"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Заголовок"}),
            "body": forms.Textarea(attrs={"class": "form-control", "rows": 6, "placeholder": "Текст поста"}),
            "is_pinned": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["full_name", "department", "phone"]
        widgets = {
            "full_name": forms.TextInput(attrs={"class": "form-control"}),
            "department": forms.TextInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
        }


class EmployeeProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["full_name", "position", "department", "phone"]
        widgets = {
            "full_name": forms.TextInput(attrs={"class": "form-control"}),
            "position": forms.Select(attrs={"class": "form-select"}),
            "department": forms.TextInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
        }


class EmployeeProfileLimitedForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["full_name", "department", "phone"]
        widgets = {
            "full_name": forms.TextInput(attrs={"class": "form-control"}),
            "department": forms.TextInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
        }


class EmployeeCreateForm(forms.Form):
    username = forms.CharField(
        label="Логин",
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )
    full_name = forms.CharField(
        label="ФИО",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    position = forms.ChoiceField(
        label="Должность",
        choices=Profile.POSITION_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"})
    )
    department = forms.CharField(
        label="Отдел",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    phone = forms.CharField(
        label="Телефон",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"})
    )

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Пользователь с таким логином уже существует.")
        return username