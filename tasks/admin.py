from django.contrib import admin
from .models import Category, Project, Task


class TaskInline(admin.TabularInline):
    """Задачи прямо на странице проекта."""
    model = Task
    extra = 0
    fields = ('title', 'status', 'priority', 'category')


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'tasks_count')
    search_fields = ('name',)
    inlines = [TaskInline]

    @admin.display(description='Задач')
    def tasks_count(self, obj):
        return obj.tasks.count()


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'priority', 'project', 'category', 'created_at')
    list_filter = ('status', 'priority', 'project', 'category')
    search_fields = ('title',)
