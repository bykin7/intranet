import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    PostForm,
    ProfileForm,
    EmployeeProfileForm,
    EmployeeProfileLimitedForm,
    EmployeeCreateForm,
)
from .models import Post, Profile, Comment
from .permissions import (
    can_create_posts,
    can_view_admin_log,
    can_manage_employees,
    can_change_position,
    can_edit_post,
    can_delete_post,
    can_delete_comment,
)

logger = logging.getLogger("happytogether")

@login_required
def feed_list(request):
    posts = Post.objects.select_related("author").prefetch_related("comments").all()

    search_query = request.GET.get("q", "").strip()
    filter_type = request.GET.get("filter", "all").strip()

    if filter_type == "important":
        posts = posts.filter(is_pinned=True)

    if search_query:
        posts = posts.filter(
            Q(title__icontains=search_query) |
            Q(body__icontains=search_query)
        )

    posts = posts.order_by("-is_pinned", "-created_at")[:50]

    return render(
        request,
        "feed/list.html",
        {
            "posts": posts,
            "search_query": search_query,
            "filter_type": filter_type,
        },
    )


@login_required
def post_create(request):
    if not can_create_posts(request.user):
        return HttpResponseForbidden("У вас нет доступа к созданию постов.")

    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()

            logger.info(
                f"POST_CREATE id={post.id} author={request.user.username} pinned={post.is_pinned}"
            )

            return redirect("feed_list")
    else:
        form = PostForm()

    return render(request, "feed/create.html", {"form": form})


def post_detail(request, post_id):
    post = get_object_or_404(Post.objects.select_related("author"), id=post_id)

    if request.method == "POST" and request.user.is_authenticated:
        body = request.POST.get("body", "").strip()
        if body:
            post.comments.create(author=request.user, body=body)

            logger.info(
                f"COMMENT_CREATE post_id={post.id} author={request.user.username}"
            )

            return redirect(request.path)

    return render(request, "feed/detail.html", {"post": post})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if not can_edit_post(request.user, post):
        return HttpResponseForbidden("У вас нет доступа к редактированию этого поста.")

    if request.method == "POST":
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            logger.info(
                f"POST_EDIT id={post.id} by={request.user.username}"
            )
            return redirect("post_detail", post_id=post.id)
    else:
        form = PostForm(instance=post)

    return render(
        request,
        "feed/post_edit.html",
        {
            "form": form,
            "post": post,
        },
    )


@login_required
def post_delete(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if not can_delete_post(request.user, post):
        return HttpResponseForbidden("У вас нет доступа к удалению этого поста.")

    if request.method == "POST":
        logger.info(
            f"POST_DELETE id={post.id} by={request.user.username}"
        )
        post.delete()
        return redirect("feed_list")

    return render(
        request,
        "feed/post_delete.html",
        {
            "post": post,
        },
    )


@login_required
def comment_delete(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    if not can_delete_comment(request.user, comment):
        return HttpResponseForbidden("У вас нет доступа к удалению этого комментария.")

    post_id = comment.post.id

    if request.method == "POST":
        logger.info(
            f"COMMENT_DELETE id={comment.id} by={request.user.username}"
        )
        comment.delete()
        return redirect("post_detail", post_id=post_id)

    return render(
        request,
        "feed/comment_delete.html",
        {
            "comment": comment,
        },
    )


@login_required
def admin_log_view(request):
    if not can_view_admin_log(request.user):
        return HttpResponseForbidden("У вас нет доступа к журналу действий.")

    log_path = settings.BASE_DIR / "logs" / "app.log"
    lines = []

    try:
        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()[-200:]
    except FileNotFoundError:
        lines = ["Лог-файл app.log не найден."]

    lines = [line.strip() for line in lines if line.strip()]
    lines.reverse()

    return render(request, "core/admin_log.html", {"lines": lines})


@login_required
def profile_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect("profile")
    else:
        form = ProfileForm(instance=profile)

    return render(request, "feed/profile.html", {"form": form})


@login_required
def employees_list(request):
    profiles = Profile.objects.select_related("user").all().order_by("full_name", "user__username")

    search_query = request.GET.get("q", "").strip()
    position_filter = request.GET.get("position", "").strip()

    if search_query:
        profiles = profiles.filter(
            Q(full_name__icontains=search_query) |
            Q(user__username__icontains=search_query)
        )

    if position_filter:
        profiles = profiles.filter(position=position_filter)

    positions = Profile.POSITION_CHOICES

    return render(
        request,
        "feed/employees_list.html",
        {
            "profiles": profiles,
            "search_query": search_query,
            "position_filter": position_filter,
            "positions": positions,
        },
    )


@login_required
def employee_create(request):
    if not can_manage_employees(request.user):
        return HttpResponseForbidden("У вас нет доступа к созданию сотрудников.")

    if request.method == "POST":
        form = EmployeeCreateForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password"],
            )

            profile, _ = Profile.objects.get_or_create(user=user)
            profile.full_name = form.cleaned_data["full_name"]
            profile.position = form.cleaned_data["position"]
            profile.department = form.cleaned_data["department"]
            profile.phone = form.cleaned_data["phone"]
            profile.save()

            logger.info(
                f"EMPLOYEE_CREATE by={request.user.username} created={user.username} position={profile.position}"
            )

            return redirect("employees")
    else:
        form = EmployeeCreateForm()

    return render(request, "feed/employee_create.html", {"form": form})


@login_required
def employee_edit(request, profile_id):
    if not can_manage_employees(request.user):
        return HttpResponseForbidden("У вас нет доступа к управлению сотрудниками.")

    profile = get_object_or_404(Profile.objects.select_related("user"), id=profile_id)

    # По умолчанию:
    # СВ и СБ могут менять должности,
    # но НЕ СВОЮ собственную
    if can_change_position(request.user) and profile.user != request.user:
        form_class = EmployeeProfileForm
        can_edit_position = True
    else:
        form_class = EmployeeProfileLimitedForm
        can_edit_position = False

    if request.method == "POST":
        form = form_class(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            logger.info(
                f"EMPLOYEE_EDIT by={request.user.username} edited={profile.user.username}"
            )
            return redirect("employees")
    else:
        form = form_class(instance=profile)

    return render(
        request,
        "feed/employee_edit.html",
        {
            "form": form,
            "profile_obj": profile,
            "can_change_position": can_edit_position,
        },
    )