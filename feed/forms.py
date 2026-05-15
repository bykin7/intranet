from django import forms
from django.contrib.auth.models import User

from .models import Post, Profile, Store



class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["title", "body", "image", "is_pinned"]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Заголовок новости",
                }
            ),
            "body": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 6,
                    "placeholder": "Текст новости",
                }
            ),
            "image": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                    "accept": "image/*",
                }
            ),
            "is_pinned": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["full_name", "phone"]
        widgets = {
            "full_name": forms.TextInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
        }

class StoreForm(forms.ModelForm):
    class Meta:
        model = Store
        fields = ["name", "address", "phone", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.TextInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

class ProfileMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        name = obj.full_name or "Без ФИО"
        position = obj.get_position_display()
        return f"{name} — {position}"


class StoreEmployeeAssignForm(forms.Form):
    main_employees = ProfileMultipleChoiceField(
        label="Сотрудники магазина",
        queryset=Profile.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple()
    )

    managers = ProfileMultipleChoiceField(
        label="Супервайзеры и служба безопасности",
        queryset=Profile.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple()
    )

    def __init__(self, *args, store=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.store = store

        one_store_positions = [
            "admin",
            "cashier",
            "loss_prevention",
            "worker",
        ]

        many_store_positions = [
            "supervisor",
            "security",
        ]

        main_employees = (
            Profile.objects
            .select_related("user", "store")
            .filter(position__in=one_store_positions)
            .order_by("position", "full_name", "user__username")
        )

        if store and store.worker_user_id:
            main_employees = main_employees.exclude(user_id=store.worker_user_id)

        managers = (
            Profile.objects
            .select_related("user")
            .filter(position__in=many_store_positions)
            .order_by("position", "full_name", "user__username")
        )

        self.fields["main_employees"].queryset = main_employees
        self.fields["managers"].queryset = managers

        if store:
            self.fields["main_employees"].initial = main_employees.filter(store=store)
            self.fields["managers"].initial = managers.filter(managed_stores=store)

    def save(self):
        store = self.store

        selected_main_employees = self.cleaned_data["main_employees"]
        selected_managers = self.cleaned_data["managers"]

        one_store_positions = [
            "admin",
            "cashier",
            "loss_prevention",
            "worker",
        ]

        many_store_positions = [
            "supervisor",
            "security",
        ]

        current_main_employees = Profile.objects.filter(
            position__in=one_store_positions,
            store=store
        )

        if store.worker_user_id:
            current_main_employees = current_main_employees.exclude(
                user_id=store.worker_user_id
            )

        selected_main_ids = selected_main_employees.values_list("id", flat=True)

        current_main_employees.exclude(id__in=selected_main_ids).update(store=None)

        selected_main_employees.update(store=store)

        current_managers = Profile.objects.filter(
            position__in=many_store_positions,
            managed_stores=store
        )

        selected_manager_ids = selected_managers.values_list("id", flat=True)

        for profile in current_managers.exclude(id__in=selected_manager_ids):
            profile.managed_stores.remove(store)

        for profile in selected_managers:
            profile.managed_stores.add(store)

class EmployeeCreateForm(forms.Form):
    username = forms.CharField(
        label="Логин",
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control"})
    )

    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )

    full_name = forms.CharField(
        label="ФИО",
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control"})
    )

    position = forms.ChoiceField(
        label="Должность",
        choices=Profile.POSITION_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"})
    )

    department = forms.CharField(
        label="Отдел",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"})
    )

    phone = forms.CharField(
        label="Телефон",
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"})
    )

    store = forms.ModelChoiceField(
        label="Основной магазин",
        queryset=Store.objects.none(),
        required=False,
        widget=forms.Select(attrs={"class": "form-select"})
    )

    managed_stores = forms.ModelMultipleChoiceField(
        label="Доступные магазины",
        queryset=Store.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple()
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        stores = Store.objects.filter(is_active=True).order_by("name")
        self.fields["store"].queryset = stores
        self.fields["managed_stores"].queryset = stores

    def clean_username(self):
        username = self.cleaned_data["username"]

        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Пользователь с таким логином уже существует.")

        return username

    def clean(self):
        cleaned_data = super().clean()

        position = cleaned_data.get("position")
        store = cleaned_data.get("store")
        managed_stores = cleaned_data.get("managed_stores")

        one_store_positions = ["admin", "cashier", "loss_prevention", "worker"]
        many_store_positions = ["supervisor", "security"]

        if position in one_store_positions and not store:
            self.add_error(
                "store",
                "Для этой должности нужно выбрать основной магазин."
            )

        if position in many_store_positions and not managed_stores:
            self.add_error(
                "managed_stores",
                "Для этой должности нужно выбрать доступные магазины."
            )

        return cleaned_data

class EmployeeEditForm(forms.ModelForm):
    new_password = forms.CharField(
    label="Новый пароль",
    required=False,
    widget=forms.PasswordInput(
        attrs={
            "class": "form-control",
            "placeholder": "Оставьте пустым, если пароль менять не нужно",
            "autocomplete": "new-password",
        }
    ),
    help_text="Оставьте поле пустым, если пароль менять не нужно.",
)

    class Meta:
        model = Profile
        fields = [
            "full_name",
            "position",
            "phone",
            "managed_stores",
        ]
        widgets = {
            "full_name": forms.TextInput(attrs={"class": "form-control"}),
            "position": forms.Select(attrs={"class": "form-select"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "managed_stores": forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, can_change_position=False, **kwargs):
        super().__init__(*args, **kwargs)

        stores = Store.objects.filter(is_active=True).order_by("name")
        self.fields["managed_stores"].queryset = stores

        if not can_change_position:
            self.fields.pop("position", None)
            self.fields.pop("managed_stores", None)

    def clean(self):
        cleaned_data = super().clean()

        position = cleaned_data.get("position")
        managed_stores = cleaned_data.get("managed_stores")

        many_store_positions = ["supervisor", "security"]

        if position in many_store_positions and not managed_stores:
            self.add_error(
                "managed_stores",
                "Для этой должности нужно выбрать доступные магазины."
            )

        return cleaned_data