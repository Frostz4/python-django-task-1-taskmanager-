import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Task

def health_check(request):
    return JsonResponse({"status": "ok"})

def home_view(request):
    return JsonResponse(
        {"message": "Добро пожаловать в Task Manager API!"}, 
        json_dumps_params={'ensure_ascii': False}
    )

def about_view(request):
    return JsonResponse(
        {"app": "Task Manager", "version": "1.0.0"}, 
        json_dumps_params={'ensure_ascii': False}
    )

# Работа со списком задач (GET - получить все, POST - создать новую)
@csrf_exempt
def task_list_view(request):
    if request.method == 'GET':
        tasks = Task.objects.all()
        data = [
            {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "status": task.status,
                "created_at": task.created_at.isoformat()
            }
            for task in tasks
        ]
        return JsonResponse(data, safe=False, json_dumps_params={'ensure_ascii': False})

    elif request.method == 'POST':
        try:
            body_data = json.loads(request.body)
            task = Task.objects.create(
                title=body_data.get('title', ''),
                description=body_data.get('description', ''),
                status=body_data.get('status', 'todo')
            )
            return JsonResponse(
                {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "status": task.status,
                    "created_at": task.created_at.isoformat()
                },
                status=201,
                json_dumps_params={'ensure_ascii': False}
            )
        except json.JSONDecodeError:
            return JsonResponse({"error": "Некорректный JSON"}, status=400, json_dumps_params={'ensure_ascii': False})

    return JsonResponse({"error": "Метод не поддерживается"}, status=405, json_dumps_params={'ensure_ascii': False})


# Работа с конкретной задачей по ID (GET, PUT, PATCH, DELETE)
@csrf_exempt
def task_detail_view(request, id):
    try:
        task = Task.objects.get(id=id)
    except Task.DoesNotExist:
        return JsonResponse({"error": "Задача не найдена"}, status=404, json_dumps_params={'ensure_ascii': False})

    # 1. Получение одной задачи
    if request.method == 'GET':
        return JsonResponse(
            {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "status": task.status,
                "created_at": task.created_at.isoformat()
            },
            json_dumps_params={'ensure_ascii': False}
        )

    # 2. Полное или частичное обновление задачи (PUT / PATCH)
    elif request.method in ['PUT', 'PATCH']:
        try:
            body_data = json.loads(request.body)
            
            if 'title' in body_data:
                task.title = body_data['title']
            if 'description' in body_data:
                task.description = body_data['description']
            if 'status' in body_data:
                task.status = body_data['status']
                
            task.save()  # Сохраняем изменения в базу данных
            
            return JsonResponse(
                {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "status": task.status,
                    "created_at": task.created_at.isoformat()
                },
                json_dumps_params={'ensure_ascii': False}
            )
        except json.JSONDecodeError:
            return JsonResponse({"error": "Некорректный JSON"}, status=400, json_dumps_params={'ensure_ascii': False})

    # 3. Удаление задачи (DELETE)
    elif request.method == 'DELETE':
        task.delete()  # Удаляем запись из БД
        return JsonResponse({"message": "Задача успешно удалена"}, status=200, json_dumps_params={'ensure_ascii': False})

    return JsonResponse({"error": "Метод не поддерживается"}, status=405, json_dumps_params={'ensure_ascii': False})


@csrf_exempt
def echo_view(request):
    if request.method != 'POST':
        return JsonResponse({"error": "Разрешен только метод POST"}, status=405)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Некорректный JSON"}, status=400)
    
    return JsonResponse(data, json_dumps_params={'ensure_ascii': False})