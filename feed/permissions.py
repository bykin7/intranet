def get_position(user):
    if not user.is_authenticated:
        return None

    try:
        return user.profile.position
    except Exception:
        return None


def is_top_level(user):
    return get_position(user) in ["supervisor", "security"]


def is_manager_level(user):
    return get_position(user) == "admin"


def can_create_posts(user):
    return get_position(user) in ["supervisor", "security", "admin"]


def can_create_tasks(user):
    return get_position(user) in ["supervisor", "security", "admin"]


def can_view_admin_log(user):
    return get_position(user) in ["supervisor", "security"]


def can_manage_employees(user):
    return get_position(user) in ["supervisor", "security", "admin"]


def can_change_position(user):
    return get_position(user) in ["supervisor", "security"]


def can_create_groups(user):
    return get_position(user) in ["supervisor", "security", "admin"]


def is_group_owner(user, group):
    return user.is_authenticated and group.owner == user


def can_create_posts(user):
    return get_position(user) == "supervisor"


def can_edit_post(user, post):
    return user.is_authenticated and get_position(user) == "supervisor"


def can_delete_post(user, post):
    return user.is_authenticated and get_position(user) == "supervisor"


def can_delete_comment(user, comment):
    if not user.is_authenticated:
        return False

    # супервайзер может удалить любой комментарий
    if get_position(user) == "supervisor":
        return True

    # остальные — только свой
    return comment.author == user