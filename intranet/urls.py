from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),

    # auth (/login/, /logout/, ...)
    path("", include("django.contrib.auth.urls")),

    # app
    path("", include("feed.urls")),
    path("tasks/", include("tasks.urls")),
    path("chat/", include("chat.urls")),
    path("notifications/", include("notifications.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)