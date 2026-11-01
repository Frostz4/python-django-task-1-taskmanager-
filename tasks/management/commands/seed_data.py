from django.core.management.base import BaseCommand

from tasks.models import Category, Project, Task


class Command(BaseCommand):
    help = 'Заполняет базу тестовыми данными (проекты, категории, задачи)'

    def handle(self, *args, **options):
        categories = {
            name: Category.objects.get_or_create(name=name, defaults={'description': desc})[0]
            for name, desc in [
                ('Backend', 'Серверная логика и API'),
                ('Frontend', 'Интерфейс пользователя'),
                ('Bugfix', 'Исправление ошибок'),
            ]
        }
        projects = {
            name: Project.objects.get_or_create(name=name, defaults={'description': desc})[0]
            for name, desc in [
                ('Task Manager', 'Учебный проект: система управления задачами'),
                ('Сайт университета', 'Новый сайт кафедры'),
            ]
        }

        # (title, status, priority, project, category)
        rows = [
            ('Создать модели', 'done', 'high', 'Task Manager', 'Backend'),
            ('Настроить админку', 'done', 'medium', 'Task Manager', 'Backend'),
            ('Сделать REST API', 'in_progress', 'high', 'Task Manager', 'Backend'),
            ('Написать README', 'todo', 'low', 'Task Manager', 'Backend'),
            ('Исправить 500 на /tasks/', 'todo', 'high', 'Task Manager', 'Bugfix'),
            ('Макет главной страницы', 'in_progress', 'medium', 'Сайт университета', 'Frontend'),
            ('Вёрстка шапки', 'todo', 'low', 'Сайт университета', 'Frontend'),
            ('Форма обратной связи', 'todo', 'medium', 'Сайт университета', 'Backend'),
        ]
        created = 0
        for title, status, priority, project, category in rows:
            _, is_new = Task.objects.get_or_create(
                title=title,
                defaults={
                    'status': status,
                    'priority': priority,
                    'project': projects[project],
                    'category': categories[category],
                },
            )
            created += is_new

        self.stdout.write(self.style.SUCCESS(
            f'Готово: проектов {Project.objects.count()}, '
            f'категорий {Category.objects.count()}, '
            f'задач {Task.objects.count()} (новых: {created})'
        ))
