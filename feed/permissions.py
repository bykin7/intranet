from django.contrib.auth.models import User

def get_position(user):
    if not user.is_authenticated:
        return None

    try:
        return user.profile.position
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

def can_manage_stores(user):
    return get_position(user) == "sysadmin"

def get_accessible_stores(user):
    if not user.is_authenticated or not hasattr(user, "profile"):
        return Store.objects.none()

    profile = user.profile

    if profile.position == "sysadmin":
        return Store.objects.all()

    if profile.position in ["supervisor", "security"]:
        return profile.managed_stores.all()

    if profile.store:
        return Store.objects.filter(id=profile.store.id)

    return Store.objects.none()

from django.db.models import Q
from .models import Profile, Store


def get_user_profile(user):
    if not user or not user.is_authenticated:
        return None

    try:
        return user.profile
    except Exception:
        return None


def get_accessible_stores(user):
    profile = get_user_profile(user)

    if not profile:
        return Store.objects.none()

    if profile.position == "sysadmin":
        return Store.objects.filter(is_active=True)

    if profile.position in ["supervisor", "security"]:
        return profile.managed_stores.filter(is_active=True)

    if profile.store:
        return Store.objects.filter(id=profile.store.id, is_active=True)

    return Store.objects.none()


def get_visible_profiles_for_user(user):
    profile = get_user_profile(user)

    if not profile:
        return Profile.objects.none()

    if profile.position == "sysadmin":
        return (
            Profile.objects
            .select_related("user", "store")
            .prefetch_related("managed_stores")
            .all()
        )

    accessible_stores = get_accessible_stores(user)

    return (
        Profile.objects
        .select_related("user", "store")
        .prefetch_related("managed_stores")
        .filter(
            Q(user=user) |

            # Обычные сотрудники, администраторы и рабочие аккаунты
            # видны только если их основной магазин входит в доступные магазины пользователя
            Q(store__in=accessible_stores) |

            # Супервайзеры и СБ видны только если у них есть пересечение
            # хотя бы по одному доступному магазину
            Q(
                position__in=["supervisor", "security"],
                managed_stores__in=accessible_stores
            )
        )
        .distinct()
    )

def can_view_post(user, post):
    profile = get_user_profile(user)

    if not profile:
        return False

    if profile.position == "sysadmin":
        return True

    if post.author == user:
        return True

    accessible_stores = get_accessible_stores(user)

    return post.stores.filter(id__in=accessible_stores.values_list("id", flat=True)).exists()

def get_visible_users_for_user(user):
    return User.objects.filter(
        profile__in=get_visible_profiles_for_user(user)
    ).distinct()