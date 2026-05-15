import logging

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import TaskForm
from .models import Task, TaskImage

logger = logging.getLogger("happytogether")


@login_required
def task_list(request):
    my_tasks = (
        Task.objects
        .select_related("assignee", "created_by", "assignee__profile", "created_by__profile")
        .prefetch_related("images")
        .filter(assignee=request.user)
    )

    created_by_me = (
        Task.objects
        .select_related("assignee", "created_by", "assignee__profile", "created_by__profile")
        .prefetch_related("images")
        .filter(created_by=request.user)
    )

    status_filter = request.GET.get("status", "").strip()
    priority_filter = request.GET.get("priority", "").strip()

    if status_filter:
        my_tasks = my_tasks.filter(status=status_filter)
        created_by_me = created_by_me.filter(status=status_filter)

    if priority_filter:
        my_tasks = my_tasks.filter(priority=priority_filter)
        created_by_me = created_by_me.filter(priority=priority_filter)

    return render(
        request,
        "tasks/list.html",
        {
            "my_tasks": my_tasks,
            "created_by_me": created_by_me,
            "status_filter": status_filter,
            "priority_filter": priority_filter,
            "statuses": Task.Status.choices,
            "priorities": Task.Priority.choices,
        },
    )


@login_required
def task_create(request):
    if request.method == "POST":
        form = TaskForm(request.POST, request.FILES, user=request.user)

        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.save()

            images = request.FILES.getlist("images")

            for image in images:
                TaskImage.objects.create(
                    task=task,
                    image=image,
                )

            logger.info(
                f"TASK_CREATE id={task.id} by={request.user.username} "
                f"to={task.assignee.username} due={task.due_date} "
                f"images={len(images)}"
            )

            return redirect(reverse("task_list"))
    else:
        form = TaskForm(user=request.user)

    return render(
        request,
        "tasks/create.html",
        {
            "form": form,
        },
    )


@login_required
def task_detail(request, task_id: int):
    task = get_object_or_404(
        Task.objects
        .select_related("assignee", "created_by", "assignee__profile", "created_by__profile")
        .prefetch_related("images"),
        id=task_id,
    )

    if not (
        request.user == task.assignee
        or request.user == task.created_by
        or request.user.is_staff
    ):
        return redirect(reverse("task_list"))

    if request.method == "POST":
        new_status = request.POST.get("status")
        images = request.FILES.getlist("images")

        allowed = {
            Task.Status.NEW,
            Task.Status.IN_PROGRESS,
            Task.Status.DONE,
        }

        if new_status in allowed:
            old = task.status
            task.status = new_status
            task.save(update_fields=["status"])

            logger.info(
                f"TASK_STATUS_CHANGE id={task.id} "
                f"by={request.user.username} {old}->{new_status}"
            )

        if images:
            for image in images:
                TaskImage.objects.create(
                    task=task,
                    image=image,
                )

            logger.info(
                f"TASK_IMAGES_ADD id={task.id} "
                f"by={request.user.username} images={len(images)}"
            )

        return redirect(reverse("task_detail", args=[task.id]))

    return render(
        request,
        "tasks/detail.html",
        {
            "task": task,
            "Status": Task.Status,
        },
    )


@login_required
def task_delete(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    if task.created_by != request.user:
        return HttpResponseForbidden("Удалить задачу может только её создатель.")

    if request.method == "POST":
        logger.info(
            f"TASK_DELETE id={task.id} by={request.user.username}"
        )

        task.delete()

        return redirect("task_list")

    return render(
        request,
        "tasks/task_delete.html",
        {
            "task": task,
        },
    )