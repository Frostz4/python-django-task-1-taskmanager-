from django.contrib import admin
from .models import Task

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    # Столбцы, которые будут отображаться в списке задач
    list_display = ('title', 'status', 'created_at')
    
    # Фильтр справа по статусу
    list_filter = ('status',)
    
    # Поле поиска по названию задачи
    search_fields = ('title',)
