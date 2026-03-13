import logging

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Q

from .models import (
    PrivateChat,
    PrivateMessage,
    PrivateChatRead,
    GroupChat,
    GroupChatMember,
    GroupChatMessage,
    GroupChatRead,
)

from .forms import (
    NewPrivateChatForm,
    GroupChatForm,
    AddGroupChatMemberForm,
)

from feed.permissions import can_create_groups, is_group_owner

logger = logging.getLogger("happytogether")


@login_required
def chat_home(request):
    private_chats = PrivateChat.objects.filter(
        Q(user1=request.user) | Q(user2=request.user)
    ).select_related("user1", "user2")

    group_chats = GroupChat.objects.filter(
        memberships__user=request.user
    ).select_related("owner").distinct()

    private_chat_data = []
    for chat in private_chats:
        other_user = chat.user2 if chat.user1 == request.user else chat.user1
        last_message = chat.messages.order_by("-created_at").first()

        read_state = PrivateChatRead.objects.filter(
            chat=chat,
            user=request.user
        ).first()

        if read_state:
            unread_count = chat.messages.filter(
                created_at__gt=read_state.last_read_at
            ).exclude(author=request.user).count()
        else:
            unread_count = chat.messages.exclude(author=request.user).count()

        private_chat_data.append({
            "chat": chat,
            "other_user": other_user,
            "last_message": last_message,
            "unread_count": unread_count,
        })

    group_chat_data = []
    for group in group_chats:
        last_message = group.messages.order_by("-created_at").first()

        read_state = GroupChatRead.objects.filter(
            group=group,
            user=request.user
        ).first()

        if read_state:
            unread_count = group.messages.filter(
                created_at__gt=read_state.last_read_at
            ).exclude(author=request.user).count()
        else:
            unread_count = group.messages.exclude(author=request.user).count()

        group_chat_data.append({
            "group": group,
            "last_message": last_message,
            "unread_count": unread_count,
        })

    private_chat_data.sort(
        key=lambda item: item["last_message"].created_at if item["last_message"] else item["chat"].created_at,
        reverse=True
    )

    group_chat_data.sort(
        key=lambda item: item["last_message"].created_at if item["last_message"] else item["group"].created_at,
        reverse=True
    )

    return render(
        request,
        "chat/chat_home.html",
        {
            "private_chat_data": private_chat_data,
            "group_chat_data": group_chat_data,
        },
    )


@login_required
def private_chat_create(request):
    if request.method == "POST":
        form = NewPrivateChatForm(request.POST)

        if form.is_valid():
            other_user = form.cleaned_data["user"]

            if other_user == request.user:
                return HttpResponseForbidden("Нельзя создать чат с самим собой.")

            user1, user2 = sorted([request.user.id, other_user.id])

            chat, created = PrivateChat.objects.get_or_create(
                user1_id=user1,
                user2_id=user2,
            )

            if created:
                logger.info(
                    f"PRIVATE_CHAT_CREATE by={request.user.username} with={other_user.username}"
                )

            return redirect("private_chat_detail", chat_id=chat.id)

    else:
        form = NewPrivateChatForm()

    return render(request, "chat/private_chat_create.html", {"form": form})


@login_required
def private_chat_detail(request, chat_id):
    chat = get_object_or_404(PrivateChat, id=chat_id)

    if request.user != chat.user1 and request.user != chat.user2:
        return HttpResponseForbidden("Нет доступа к этому чату.")

    messages = chat.messages.select_related("author").all()

    # помечаем чат как прочитанный
    PrivateChatRead.objects.update_or_create(
        chat=chat,
        user=request.user,
        defaults={}
    )

    if request.method == "POST":
        body = request.POST.get("body", "").strip()

        if body:
            PrivateMessage.objects.create(
                chat=chat,
                author=request.user,
                body=body,
            )

            logger.info(
                f"PRIVATE_MESSAGE chat={chat.id} author={request.user.username}"
            )

            return redirect("private_chat_detail", chat_id=chat.id)

    other_user = chat.user2 if request.user == chat.user1 else chat.user1

    return render(
        request,
        "chat/private_chat_detail.html",
        {
            "chat": chat,
            "messages": messages,
            "other_user": other_user,
        },
    )


@login_required
def private_message_delete(request, message_id):
    message = get_object_or_404(PrivateMessage, id=message_id)
    chat = message.chat

    if message.author != request.user:
        return HttpResponseForbidden("Вы можете удалить только своё сообщение.")

    if request.method == "POST":
        logger.info(
            f"PRIVATE_MESSAGE_DELETE id={message.id} by={request.user.username}"
        )
        message.delete()
        return redirect("private_chat_detail", chat_id=chat.id)

    return render(
        request,
        "chat/private_message_delete.html",
        {
            "message": message,
            "chat": chat,
        },
    )


@login_required
def group_chat_create(request):
    if not can_create_groups(request.user):
        return HttpResponseForbidden("Нет доступа к созданию группы.")

    if request.method == "POST":
        form = GroupChatForm(request.POST)

        if form.is_valid():
            group = form.save(commit=False)
            group.owner = request.user
            group.save()

            GroupChatMember.objects.create(
                group=group,
                user=request.user,
            )

            GroupChatRead.objects.get_or_create(
                group=group,
                user=request.user,
            )

            logger.info(
                f"GROUP_CHAT_CREATE by={request.user.username} group={group.name}"
            )

            return redirect("group_chat_detail", group_id=group.id)

    else:
        form = GroupChatForm()

    return render(request, "chat/group_chat_create.html", {"form": form})


@login_required
def group_chat_detail(request, group_id):
    group = get_object_or_404(GroupChat, id=group_id)

    is_member = GroupChatMember.objects.filter(
        group=group,
        user=request.user
    ).exists()

    if not is_member:
        return HttpResponseForbidden("Вы не участник этой группы.")

    messages = group.messages.select_related("author").all()
    members = group.memberships.select_related("user").all()

    # помечаем группу как прочитанную
    GroupChatRead.objects.update_or_create(
        group=group,
        user=request.user,
        defaults={}
    )

    if request.method == "POST":
        body = request.POST.get("body", "").strip()

        if body:
            GroupChatMessage.objects.create(
                group=group,
                author=request.user,
                body=body,
            )

            logger.info(
                f"GROUP_CHAT_MESSAGE group={group.id} author={request.user.username}"
            )

            return redirect("group_chat_detail", group_id=group.id)

    return render(
        request,
        "chat/group_chat_detail.html",
        {
            "group": group,
            "messages": messages,
            "members": members,
            "is_owner": is_group_owner(request.user, group),
        },
    )


@login_required
def group_chat_add_member(request, group_id):
    group = get_object_or_404(GroupChat, id=group_id)

    if not is_group_owner(request.user, group):
        return HttpResponseForbidden("Только владелец может добавлять участников.")

    if request.method == "POST":
        form = AddGroupChatMemberForm(request.POST)

        if form.is_valid():
            user = form.cleaned_data["user"]

            GroupChatMember.objects.get_or_create(
                group=group,
                user=user
            )

            GroupChatRead.objects.get_or_create(
                group=group,
                user=user
            )

            logger.info(
                f"GROUP_MEMBER_ADD by={request.user.username} group={group.id} user={user.username}"
            )

            return redirect("group_chat_detail", group_id=group.id)

    else:
        form = AddGroupChatMemberForm()

    return render(
        request,
        "chat/group_chat_add_member.html",
        {
            "form": form,
            "group": group,
        },
    )


@login_required
def group_chat_remove_member(request, group_id, member_id):
    group = get_object_or_404(GroupChat, id=group_id)

    if not is_group_owner(request.user, group):
        return HttpResponseForbidden("Только владелец может удалять участников.")

    membership = get_object_or_404(GroupChatMember, id=member_id)

    if membership.user == group.owner:
        return HttpResponseForbidden("Нельзя удалить владельца.")

    if request.method == "POST":
        logger.info(
            f"GROUP_MEMBER_REMOVE by={request.user.username} group={group.id} user={membership.user.username}"
        )
        membership.delete()
        return redirect("group_chat_detail", group_id=group.id)

    return render(
        request,
        "chat/group_chat_remove_member.html",
        {
            "membership": membership,
            "group": group,
        },
    )


@login_required
def group_chat_delete(request, group_id):
    group = get_object_or_404(GroupChat, id=group_id)

    if not is_group_owner(request.user, group):
        return HttpResponseForbidden("Только владелец может удалить группу.")

    if request.method == "POST":
        logger.info(
            f"GROUP_DELETE by={request.user.username} group={group.id}:{group.name}"
        )
        group.delete()
        return redirect("chat_home")

    return render(
        request,
        "chat/group_chat_delete.html",
        {"group": group},
    )


@login_required
def group_message_delete(request, message_id):
    message = get_object_or_404(GroupChatMessage, id=message_id)
    group = message.group

    is_member = GroupChatMember.objects.filter(group=group, user=request.user).exists()
    if not is_member:
        return HttpResponseForbidden("Вы не участник этой группы.")

    is_owner = group.owner == request.user
    is_author = message.author == request.user

    if not (is_owner or is_author):
        return HttpResponseForbidden("У вас нет доступа к удалению этого сообщения.")

    if request.method == "POST":
        logger.info(
            f"GROUP_MESSAGE_DELETE id={message.id} by={request.user.username}"
        )
        message.delete()
        return redirect("group_chat_detail", group_id=group.id)

    return render(
        request,
        "chat/group_message_delete.html",
        {
            "message": message,
            "group": group,
        },
    )