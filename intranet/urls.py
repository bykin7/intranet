from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),

    # auth (/login/, /logout/, ...)
    path("", include("django.contrib.auth.urls")),

    # app
    path("", include("feed.urls")),
    path("tasks/", include("tasks.urls")),
    path("chat/", include("chat.urls")),
]
