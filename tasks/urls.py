from django.urls import path
from .views import task_list, task_create, task_detail, task_delete

urlpatterns = [
    path("", task_list, name="task_list"),
    path("new/", task_create, name="task_create"),
    path("<int:task_id>/", task_detail, name="task_detail"),
    path("<int:task_id>/delete/", task_delete, name="task_delete"),
]