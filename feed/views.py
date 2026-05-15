import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q, Count
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    PostForm,
    ProfileForm,
    EmployeeCreateForm,
    EmployeeEditForm,
    StoreForm,
    StoreEmployeeAssignForm,
)

from .models import (
    Post,
    Comment,
    Profile,
    Store,
    PostImage,
)

from .permissions import (
    can_create_posts,
    can_view_admin_log,
    can_manage_employees,
    can_manage_stores,
    can_change_position,
    can_edit_post,
    can_delete_post,
    can_delete_comment,
    get_accessible_stores,
    get_visible_profiles_for_user,
    can_view_post,
)

logger = logging.getLogger("happytogether")


def create_store_worker_account(store):
    username = f"store_{store.id}"
    default_password = f"store{store.id}123"

    user, created = User.objects.get_or_create(username=username)

    if created:
        user.set_password(default_password)

    user.first_name = "Рабочий"
    user.last_name = store.name
    user.save()

    profile, _ = Profile.objects.get_or_create(user=user)
    profile.full_name = f"Рабочий {store.name}"
    profile.position = "worker"
    profile.department = "Рабочий телефон"
    profile.phone = store.phone
    profile.store = store
    profile.save()

    store.worker_user = user
    store.save(update_fields=["worker_user"])

    return user


@login_required
def feed_list(request):
    posts = (
        Post.objects
        .select_related("author", "author__profile")
        .prefetch_related("comments", "stores", "images")
        .all()
    )

    if request.user.profile.position != "sysadmin":
        accessible_stores = get_accessible_stores(request.user)

        posts = posts.filter(
            stores__in=accessible_stores
        ).distinct()

    search_query = request.GET.get("q", "").strip()
    filter_type = request.GET.get("filter", "all").strip()

    if filter_type == "important":
        posts = posts.filter(is_pinned=True)

    if search_query:
        posts = posts.filter(
            Q(title__icontains=search_query)
            | Q(body__icontains=search_query)
        )

    posts = posts.order_by("-is_pinned", "-created_at")

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
        form = PostForm(request.POST, request.FILES)

        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()

            post.stores.set(get_accessible_stores(request.user))

            for image in request.FILES.getlist("images"):
                PostImage.objects.create(
                    post=post,
                    image=image,
                )

            logger.info(
                f"POST_CREATE id={post.id} author={request.user.username} pinned={post.is_pinned}"
            )

            return redirect("feed_list")
    else:
        form = PostForm()

    return render(
        request,
        "feed/create.html",
        {
            "form": form,
        },
    )


@login_required
def post_detail(request, post_id):
    post = get_object_or_404(
        Post.objects
        .select_related("author", "author__profile")
        .prefetch_related("comments", "stores", "images"),
        id=post_id,
    )

    if not can_view_post(request.user, post):
        return HttpResponseForbidden("У вас нет доступа к этому посту.")

    if request.method == "POST":
        body = request.POST.get("body", "").strip()

        if body:
            post.comments.create(author=request.user, body=body)

            logger.info(
                f"COMMENT_CREATE post_id={post.id} author={request.user.username}"
            )

            return redirect("post_detail", post_id=post.id)

    return render(
        request,
        "feed/detail.html",
        {
            "post": post,
        },
    )


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(
        Post.objects.prefetch_related("stores", "images"),
        id=post_id,
    )

    if not can_view_post(request.user, post):
        return HttpResponseForbidden("У вас нет доступа к этому посту.")

    if not can_edit_post(request.user, post):
        return HttpResponseForbidden("У вас нет доступа к редактированию этого поста.")

    if request.method == "POST":
        form = PostForm(request.POST, request.FILES, instance=post)

        if form.is_valid():
            post = form.save(commit=False)
            post.save()

            for image in request.FILES.getlist("images"):
                PostImage.objects.create(
                    post=post,
                    image=image,
                )

            if post.author.profile.position == "supervisor":
                post.stores.set(get_accessible_stores(post.author))

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
    post = get_object_or_404(
        Post.objects.prefetch_related("stores"),
        id=post_id,
    )

    if not can_view_post(request.user, post):
        return HttpResponseForbidden("У вас нет доступа к этому посту.")

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
    comment = get_object_or_404(
        Comment.objects.select_related("post", "author"),
        id=comment_id,
    )

    if not can_view_post(request.user, comment.post):
        return HttpResponseForbidden("У вас нет доступа к этому посту.")

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

    return render(
        request,
        "core/admin_log.html",
        {
            "lines": lines,
        },
    )


@login_required
def profile_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile)

        if form.is_valid():
            form.save()

            logger.info(
                f"PROFILE_EDIT user={request.user.username}"
            )

            return redirect("profile")
    else:
        form = ProfileForm(instance=profile)

    return render(
        request,
        "feed/profile.html",
        {
            "form": form,
            "profile": profile,
        },
    )


@login_required
def employees_list(request):
    profiles = (
        get_visible_profiles_for_user(request.user)
        .order_by("full_name", "user__username")
    )

    search_query = request.GET.get("q", "").strip()
    position_filter = request.GET.get("position", "").strip()
    store_filter = request.GET.get("store", "").strip()

    if search_query:
        profiles = profiles.filter(
            Q(full_name__icontains=search_query)
            | Q(user__username__icontains=search_query)
            | Q(user__first_name__icontains=search_query)
            | Q(user__last_name__icontains=search_query)
        )

    if position_filter:
        profiles = profiles.filter(position=position_filter)

    if store_filter:
        profiles = profiles.filter(
            Q(store_id=store_filter)
            | Q(managed_stores__id=store_filter)
        ).distinct()

    positions = Profile.POSITION_CHOICES
    stores = Store.objects.filter(is_active=True).order_by("name")

    return render(
        request,
        "feed/employees_list.html",
        {
            "profiles": profiles,
            "search_query": search_query,
            "position_filter": position_filter,
            "store_filter": store_filter,
            "positions": positions,
            "stores": stores,
        },
    )


@login_required
def stores_list(request):
    if not can_manage_stores(request.user):
        return HttpResponseForbidden(
            "Только системный администратор может управлять магазинами."
        )

    stores = (
        Store.objects
        .select_related("worker_user")
        .annotate(employee_count=Count("employees"))
        .order_by("name")
    )

    return render(
        request,
        "feed/stores_list.html",
        {
            "stores": stores,
        },
    )


@login_required
def store_detail(request, store_id):
    if not can_manage_stores(request.user):
        return HttpResponseForbidden(
            "Только системный администратор может просматривать магазины."
        )

    store = get_object_or_404(
        Store.objects.select_related("worker_user"),
        id=store_id,
    )

    employees = (
        store.employees
        .select_related("user")
        .order_by("position", "full_name", "user__username")
    )

    managers = (
        store.managers
        .select_related("user")
        .order_by("position", "full_name", "user__username")
    )

    return render(
        request,
        "feed/store_detail.html",
        {
            "store": store,
            "employees": employees,
            "managers": managers,
        },
    )


@login_required
def store_create(request):
    if not can_manage_stores(request.user):
        return HttpResponseForbidden(
            "Только системный администратор может создавать магазины."
        )

    if request.method == "POST":
        form = StoreForm(request.POST)

        if form.is_valid():
            store = form.save()
            create_store_worker_account(store)

            logger.info(
                f"STORE_CREATE id={store.id} name={store.name} by={request.user.username}"
            )

            return redirect("store_detail", store_id=store.id)
    else:
        form = StoreForm()

    return render(
        request,
        "feed/store_form.html",
        {
            "form": form,
            "title": "Новый магазин",
            "button_text": "Создать магазин",
        },
    )


@login_required
def store_edit(request, store_id):
    if not can_manage_stores(request.user):
        return HttpResponseForbidden(
            "Только системный администратор может редактировать магазины."
        )

    store = get_object_or_404(Store, id=store_id)

    if request.method == "POST":
        form = StoreForm(request.POST, instance=store)

        if form.is_valid():
            store = form.save()

            if store.worker_user:
                store.worker_user.first_name = "Рабочий"
                store.worker_user.last_name = store.name
                store.worker_user.save()

                profile, _ = Profile.objects.get_or_create(user=store.worker_user)
                profile.full_name = f"Рабочий {store.name}"
                profile.position = "worker"
                profile.department = "Рабочий телефон"
                profile.phone = store.phone
                profile.store = store
                profile.save()
            else:
                create_store_worker_account(store)

            logger.info(
                f"STORE_EDIT id={store.id} name={store.name} by={request.user.username}"
            )

            return redirect("store_detail", store_id=store.id)
    else:
        form = StoreForm(instance=store)

    return render(
        request,
        "feed/store_form.html",
        {
            "form": form,
            "title": "Редактирование магазина",
            "button_text": "Сохранить",
            "store": store,
        },
    )


@login_required
def store_assign_employees(request, store_id):
    if not can_manage_stores(request.user):
        return HttpResponseForbidden(
            "Только системный администратор может распределять сотрудников по магазинам."
        )

    store = get_object_or_404(Store, id=store_id)

    if request.method == "POST":
        form = StoreEmployeeAssignForm(request.POST, store=store)

        if form.is_valid():
            form.save()

            logger.info(
                f"STORE_ASSIGN_EMPLOYEES store_id={store.id} "
                f"name={store.name} by={request.user.username}"
            )

            return redirect("store_detail", store_id=store.id)
    else:
        form = StoreEmployeeAssignForm(store=store)

    return render(
        request,
        "feed/store_assign_employees.html",
        {
            "store": store,
            "form": form,
        },
    )


@login_required
def employee_create(request):
    if not can_manage_employees(request.user):
        return HttpResponseForbidden(
            "Только системный администратор может создавать сотрудников."
        )

    if request.method == "POST":
        form = EmployeeCreateForm(request.POST)

        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password"],
            )

            profile, _ = Profile.objects.get_or_create(user=user)

            profile.full_name = form.cleaned_data.get("full_name", "")
            profile.position = form.cleaned_data.get("position", "")
            profile.department = form.cleaned_data.get("department", "")
            profile.phone = form.cleaned_data.get("phone", "")
            profile.store = form.cleaned_data.get("store")
            profile.save()

            managed_stores = form.cleaned_data.get("managed_stores")
            if managed_stores is not None:
                profile.managed_stores.set(managed_stores)

            logger.info(
                f"EMPLOYEE_CREATE user={user.username} "
                f"position={profile.position} by={request.user.username}"
            )

            return redirect("employees")
    else:
        form = EmployeeCreateForm()

    return render(
        request,
        "feed/employee_create.html",
        {
            "form": form,
        },
    )


@login_required
def employee_edit(request, profile_id):
    if not can_manage_employees(request.user):
        return HttpResponseForbidden(
            "Только системный администратор может редактировать сотрудников."
        )

    try:
        profile_obj = (
            Profile.objects
            .select_related("user", "store")
            .prefetch_related("managed_stores")
            .get(id=profile_id)
        )
    except Profile.DoesNotExist:
        profile_obj = get_object_or_404(
            Profile.objects
            .select_related("user", "store")
            .prefetch_related("managed_stores"),
            user_id=profile_id,
        )

    can_change_pos = can_change_position(request.user)

    if request.method == "POST":
        form = EmployeeEditForm(
            request.POST,
            instance=profile_obj,
            can_change_position=can_change_pos,
        )

        if form.is_valid():
            profile = form.save()

            new_password = form.cleaned_data.get("new_password")
            if new_password:
                profile.user.set_password(new_password)
                profile.user.save()

            logger.info(
                f"EMPLOYEE_EDIT user={profile.user.username} by={request.user.username}"
            )

            return redirect("employees")
    else:
        form = EmployeeEditForm(
            instance=profile_obj,
            can_change_position=can_change_pos,
        )

    return render(
        request,
        "feed/employee_edit.html",
        {
            "form": form,
            "profile": profile_obj,
            "profile_obj": profile_obj,
            "can_change_position": can_change_pos,
        },
    )