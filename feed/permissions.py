from django.contrib.auth.models import User
from django.db.models import Q

from .models import Profile, Store


def get_position(user):
    if not user or not user.is_authenticated:
        return None

    try:
        return user.profile.position
    except Exception:
        return None


def get_user_profile(user):
    if not user or not user.is_authenticated:
        return None

    try:
        return user.profile
    except Exception:
        return None


def is_sysadmin(user):
    return get_position(user) == "sysadmin"


def is_basic_employee(user):
    return get_position(user) in ["cashier", "loss_prevention", "worker"]


def is_top_level(user):
    return get_position(user) in ["supervisor", "security"]


def is_manager_level(user):
    return get_position(user) == "admin"


def can_create_posts(user):
    return get_position(user) == "supervisor"


def can_create_tasks(user):
    return get_position(user) in ["supervisor", "security", "admin"]


def can_view_admin_log(user):
    return is_sysadmin(user)


def can_manage_employees(user):
    return is_sysadmin(user)


def can_change_position(user):
    return is_sysadmin(user)


def can_manage_stores(user):
    return is_sysadmin(user)


def can_create_groups(user):
    return get_position(user) in ["supervisor", "security", "admin"]


def is_group_owner(user, group):
    return user.is_authenticated and group.owner == user


def can_edit_post(user, post):
    return user.is_authenticated and (
        get_position(user) == "supervisor" or post.author == user
    )


def can_delete_post(user, post):
    return user.is_authenticated and (
        get_position(user) == "supervisor" or post.author == user
    )


def can_delete_comment(user, comment):
    if not user.is_authenticated:
        return False

    if get_position(user) == "supervisor":
        return True

    return comment.author == user


def get_accessible_stores(user):
    """
    Какие магазины доступны пользователю.

    sysadmin - все магазины.
    supervisor/security - магазины из managed_stores.
    admin - только свой магазин.
    cashier/loss_prevention/worker - магазины своего супервайзера/СБ.
    """

    profile = get_user_profile(user)

    if not profile:
        return Store.objects.none()

    if user.is_superuser or profile.position == "sysadmin":
        return Store.objects.filter(is_active=True)

    if profile.position in ["supervisor", "security"]:
        stores = profile.managed_stores.filter(is_active=True)

        if stores.exists():
            return stores

        if profile.store_id:
            return Store.objects.filter(id=profile.store_id, is_active=True)

        return Store.objects.none()

    if profile.position == "admin":
        if profile.store_id:
            return Store.objects.filter(id=profile.store_id, is_active=True)

        return Store.objects.none()

    if profile.position in ["cashier", "loss_prevention", "worker"]:
        if not profile.store_id:
            return Store.objects.none()

        managers = Profile.objects.filter(
            position__in=["supervisor", "security"],
            managed_stores=profile.store,
        )

        stores = Store.objects.filter(
            is_active=True,
            managers__in=managers,
        ).distinct()

        if stores.exists():
            return stores

        return Store.objects.filter(id=profile.store_id, is_active=True)

    if profile.store_id:
        return Store.objects.filter(id=profile.store_id, is_active=True)

    return Store.objects.none()


def get_visible_profiles_for_user(user, include_self=True):
    """
    Какие профили сотрудников видит пользователь.
    """

    profile = get_user_profile(user)

    if not profile:
        return Profile.objects.none()

    if user.is_superuser or profile.position == "sysadmin":
        profiles = (
            Profile.objects
            .select_related("user", "store")
            .prefetch_related("managed_stores")
            .all()
        )
    else:
        accessible_stores = get_accessible_stores(user)

        profiles = (
            Profile.objects
            .select_related("user", "store")
            .prefetch_related("managed_stores")
            .filter(
                Q(user=user) |
                Q(store__in=accessible_stores) |
                Q(
                    position__in=["supervisor", "security"],
                    managed_stores__in=accessible_stores,
                )
            )
            .distinct()
        )

    if not include_self:
        profiles = profiles.exclude(user=user)

    return profiles


def get_visible_users_for_user(user, include_self=True):
    """
    Каких пользователей можно видеть/выбирать в задачах и чатах.
    """

    profiles = get_visible_profiles_for_user(user, include_self=include_self)

    return (
        User.objects
        .filter(profile__in=profiles, is_active=True)
        .select_related("profile")
        .order_by("profile__full_name", "username")
        .distinct()
    )


def can_user_see_user(user, other_user):
    if not user or not other_user:
        return False

    if user == other_user:
        return True

    return get_visible_users_for_user(user, include_self=False).filter(
        id=other_user.id
    ).exists()


def can_view_post(user, post):
    profile = get_user_profile(user)

    if not profile:
        return False

    if user.is_superuser or profile.position == "sysadmin":
        return True

    if post.author == user:
        return True

    accessible_stores = get_accessible_stores(user)

    # Если новость без выбранных магазинов - считаем общей
    if not post.stores.exists():
        return True

    return post.stores.filter(
        id__in=accessible_stores.values_list("id", flat=True)
    ).exists()