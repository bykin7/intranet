from django import template

register = template.Library()


@register.filter
def position_badge_class(value):
    mapping = {
        "supervisor": "text-bg-danger",
        "security": "text-bg-dark",
        "admin": "text-bg-primary",
        "cashier": "text-bg-success",
        "loss_prevention": "text-bg-warning",
    }
    return mapping.get(value, "text-bg-secondary")


@register.filter
def task_status_badge_class(value):
    mapping = {
        "new": "text-bg-primary",
        "in_progress": "text-bg-warning",
        "done": "text-bg-success",
    }
    return mapping.get(value, "text-bg-secondary")


@register.filter
def task_priority_badge_class(value):
    mapping = {
        "low": "text-bg-success",
        "medium": "text-bg-warning",
        "high": "text-bg-danger",
    }
    return mapping.get(value, "text-bg-secondary")