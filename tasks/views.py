import json
from django.http import HttpResponse, JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from .models import Category, Project, Task

JSON_PARAMS = {'ensure_ascii': False}

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

# =====================================================================
#  ПР 6. REST API и CRUD для сущности Task
# =====================================================================
#  CSRF-защита НЕ отключена. Для небезопасных методов (POST/PUT/PATCH/DELETE)
#  клиент должен: 1) получить cookie `csrftoken` запросом GET /api/csrf/,
#  2) передавать его значение в заголовке X-CSRFToken.
# =====================================================================

def json_error(message, status, details=None):
    body = {"error": message}
    if details:
        body["details"] = details
    return JsonResponse(body, status=status, json_dumps_params=JSON_PARAMS)


def serialize_task(task):
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "priority": task.priority,
        "project": task.project_id,
        "category": task.category_id,
        "created_at": task.created_at.isoformat(),
    }


def parse_json_object(request):
    """Возвращает (dict, None) или (None, JsonResponse с ошибкой 400)."""
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None, json_error("Некорректный JSON", 400)
    if not isinstance(data, dict):
        return None, json_error("Тело запроса должно быть JSON-объектом", 400)
    return data, None


def validate_task_data(data, partial=False):
    """
    Проверяет данные задачи.
    partial=False (POST, PUT) — title обязателен;
    partial=True  (PATCH)     — проверяются только переданные поля.
    Возвращает (cleaned, errors).
    """
    cleaned, errors = {}, {}

    if "title" in data or not partial:
        title = data.get("title")
        if not isinstance(title, str) or not title.strip():
            errors["title"] = "Обязательное поле: непустая строка"
        elif len(title.strip()) > 200:
            errors["title"] = "Максимум 200 символов"
        else:
            cleaned["title"] = title.strip()

    if "description" in data:
        if not isinstance(data["description"], str):
            errors["description"] = "Должна быть строкой"
        else:
            cleaned["description"] = data["description"]

    for field, choices in (("status", Task.STATUS_CHOICES), ("priority", Task.PRIORITY_CHOICES)):
        if field in data:
            allowed = [value for value, _ in choices]
            if data[field] not in allowed:
                errors[field] = f"Допустимые значения: {', '.join(allowed)}"
            else:
                cleaned[field] = data[field]

    for field, model in (("project", Project), ("category", Category)):
        if field in data:
            value = data[field]
            if value is None:
                cleaned[f"{field}_id"] = None
            elif isinstance(value, bool) or not isinstance(value, int):
                errors[field] = "Должен быть числовой id или null"
            elif not model.objects.filter(pk=value).exists():
                errors[field] = f"{model.__name__} с id={value} не существует"
            else:
                cleaned[f"{field}_id"] = value

    return cleaned, errors


@ensure_csrf_cookie
def csrf_view(request):
    """GET /api/csrf/ — выдаёт cookie csrftoken (токен также в теле ответа)."""
    return JsonResponse({"csrfToken": get_token(request)})


# GET /tasks/ — список, POST /tasks/ — создание
def task_list_view(request):
    if request.method == 'GET':
        return JsonResponse(
            [serialize_task(t) for t in Task.objects.all()],
            safe=False, json_dumps_params=JSON_PARAMS,
        )

    if request.method == 'POST':
        data, error = parse_json_object(request)
        if error:
            return error
        cleaned, errors = validate_task_data(data)
        if errors:
            return json_error("Ошибка валидации", 400, errors)
        task = Task.objects.create(**cleaned)
        return JsonResponse(serialize_task(task), status=201, json_dumps_params=JSON_PARAMS)

    response = json_error("Метод не поддерживается", 405)
    response["Allow"] = "GET, POST"
    return response


# GET / PUT / PATCH / DELETE /tasks/<id>/
def task_detail_view(request, id):
    try:
        task = Task.objects.get(id=id)
    except Task.DoesNotExist:
        return json_error("Задача не найдена", 404)

    if request.method == 'GET':
        return JsonResponse(serialize_task(task), json_dumps_params=JSON_PARAMS)

    if request.method in ('PUT', 'PATCH'):
        data, error = parse_json_object(request)
        if error:
            return error
        partial = request.method == 'PATCH'
        cleaned, errors = validate_task_data(data, partial=partial)
        if errors:
            return json_error("Ошибка валидации", 400, errors)

        if not partial:
            # PUT — полная замена: необязательные поля, которых нет в теле, сбрасываются
            defaults = {"description": "", "status": "todo", "priority": "medium",
                        "project_id": None, "category_id": None}
            for field, value in defaults.items():
                cleaned.setdefault(field, value)

        for field, value in cleaned.items():
            setattr(task, field, value)
        task.save()
        return JsonResponse(serialize_task(task), json_dumps_params=JSON_PARAMS)

    if request.method == 'DELETE':
        task.delete()
        return HttpResponse(status=204)

    response = json_error("Метод не поддерживается", 405)
    response["Allow"] = "GET, PUT, PATCH, DELETE"
    return response


@csrf_exempt
def echo_view(request):
    if request.method != 'POST':
        return JsonResponse({"error": "Разрешен только метод POST"}, status=405)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Некорректный JSON"}, status=400)
    
    return JsonResponse(data, json_dumps_params={'ensure_ascii': False})