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