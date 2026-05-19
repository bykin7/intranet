from django.db.models import Q
from django.contrib.auth.models import User

from .models import Profile, Store


def get_user_profile(user):
    try:
        return user.profile
    except Profile.DoesNotExist:
        return None


def get_available_stores_for_user(user):
    """
    Возвращает магазины, которые доступны пользователю.
    """
    profile = get_user_profile(user)

    if not profile:
        return Store.objects.none()

    if user.is_superuser or profile.position == "sysadmin":
        return Store.objects.all()

    if profile.position in ["supervisor", "security"]:
        stores = profile.managed_stores.all()

        if stores.exists():
            return stores

        if profile.store_id:
            return Store.objects.filter(id=profile.store_id)

        return Store.objects.none()

    if profile.position == "admin":
        if profile.store_id:
            return Store.objects.filter(id=profile.store_id)
        return Store.objects.none()

    if profile.position in ["cashier", "loss_prevention", "worker"]:
        if not profile.store_id:
            return Store.objects.none()

        manager_profiles = Profile.objects.filter(
            position__in=["supervisor", "security"],
            managed_stores=profile.store,
        )

        stores = Store.objects.filter(
            managers__in=manager_profiles
        ).distinct()

        if stores.exists():
            return stores

        return Store.objects.filter(id=profile.store_id)

    if profile.store_id:
        return Store.objects.filter(id=profile.store_id)

    return Store.objects.none()


def get_visible_profiles_for_user(user, include_self=True):
    """
    Возвращает профили сотрудников, которых пользователь может видеть.
    """
    profile = get_user_profile(user)

    if not profile:
        return Profile.objects.none()

    if user.is_superuser or profile.position == "sysadmin":
        qs = Profile.objects.select_related("user", "store").prefetch_related("managed_stores").all()
    else:
        stores = get_available_stores_for_user(user)

        qs = Profile.objects.select_related("user", "store").prefetch_related("managed_stores").filter(
            Q(store__in=stores) |
            Q(managed_stores__in=stores)
        ).distinct()

    if not include_self:
        qs = qs.exclude(user=user)

    return qs


def get_visible_users_for_user(user, include_self=False):
    profiles = get_visible_profiles_for_user(user, include_self=include_self)
    return User.objects.filter(
        profile__in=profiles,
        is_active=True
    ).order_by("profile__full_name", "username")


def can_user_see_user(user, other_user):
    if user == other_user:
        return True

    return get_visible_users_for_user(user, include_self=False).filter(
        id=other_user.id
    ).exists()