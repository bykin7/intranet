import logging
logger = logging.getLogger("happytogether")
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.http import HttpResponseForbidden
from feed.permissions import can_create_tasks
from .forms import TaskForm
from .models import Task


@login_required
def task_list(request):
    my_tasks = Task.objects.select_related("assignee", "created_by").filter(assignee=request.user)
    created_by_me = Task.objects.select_related("assignee", "created_by").filter(created_by=request.user)

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
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.save()
            logger.info(f"TASK_CREATE id={task.id} by={request.user.username} to={task.assignee.username} due={task.due_date}")
            return redirect(reverse("task_list"))
    else:
        form = TaskForm()

    return render(request, "tasks/create.html", {"form": form})


@login_required
def task_detail(request, task_id: int):
    task = get_object_or_404(Task.objects.select_related("assignee", "created_by"), id=task_id)

    # доступ: исполнитель, постановщик, либо staff
    if not (request.user == task.assignee or request.user == task.created_by or request.user.is_staff):
        return redirect(reverse("task_list"))

    if request.method == "POST":
        new_status = request.POST.get("status")
        allowed = {Task.Status.NEW, Task.Status.IN_PROGRESS, Task.Status.DONE}
        if new_status in allowed:
            task.status = new_status
            old = task.status
            task.status = new_status
            task.save()
            logger.info(f"TASK_STATUS_CHANGE id={task.id} by={request.user.username} {old}->{new_status}")
            task.save()
        return redirect(reverse("task_detail", args=[task.id]))

    return render(request, "tasks/detail.html", {"task": task, "Status": Task.Status})

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from .models import Task


@login_required
def task_delete(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    if task.created_by != request.user:
        return HttpResponseForbidden("Удалить задачу может только её создатель.")

    if request.method == "POST":
        task.delete()
        return redirect("task_list")

    return render(
        request,
        "tasks/task_delete.html",
        {"task": task},
    )
