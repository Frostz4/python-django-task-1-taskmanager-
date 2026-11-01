from django.db import models


class Project(models.Model):
    """Проект — контейнер для задач (1 проект : N задач)."""
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Category(models.Model):
    """Категория задач, например «Backend», «Дизайн», «Баги» (1 категория : N задач)."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, default='')

    class Meta:
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name


class Task(models.Model):
    STATUS_CHOICES = [
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
    ]
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    created_at = models.DateTimeField(auto_now_add=True)

    # Связи (null=True, чтобы не потерять уже существующие задачи при миграции)
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='tasks', null=True, blank=True
    )
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, related_name='tasks', null=True, blank=True
    )

    def __str__(self):
        return self.title
