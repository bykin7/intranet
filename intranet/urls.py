from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve

urlpatterns = [
    path("admin/", admin.site.urls),

    # auth (/login/, /logout/, ...)
    path("", include("django.contrib.auth.urls")),

    # app
    path("", include("feed.urls")),
    path("tasks/", include("tasks.urls")),
    path("chat/", include("chat.urls")),
    path("notifications/", include("notifications.urls")),

    # media files on Railway
    re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
]