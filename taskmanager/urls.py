from django.contrib import admin
from django.urls import path
from tasks.views import (
    health_check, home_view, about_view, 
    task_list_view, task_detail_view, echo_view
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health_check),
    path('', home_view),
    path('about/', about_view),
    path('tasks/', task_list_view),
    path('tasks/<int:id>/', task_detail_view),
    path('echo/', echo_view),
]