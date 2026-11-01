import json

from django.test import Client, TestCase

from .models import Category, Project, Task


class TaskApiTests(TestCase):
    """Проверка CRUD API с включённой CSRF-защитой."""

    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        token = self.client.get('/api/csrf/').json()['csrfToken']
        self.h = {'HTTP_X_CSRFTOKEN': token}
        self.project = Project.objects.create(name='P1')
        self.category = Category.objects.create(name='C1')

    def post(self, body, **extra):
        return self.client.post('/tasks/', data=body, content_type='application/json', **{**self.h, **extra})

    # --- CSRF ---
    def test_post_without_csrf_token_is_forbidden(self):
        r = Client(enforce_csrf_checks=True).post(
            '/tasks/', data={'title': 'x'}, content_type='application/json')
        self.assertEqual(r.status_code, 403)

    # --- GET ---
    def test_list_and_detail(self):
        t = Task.objects.create(title='A')
        self.assertEqual(len(self.client.get('/tasks/').json()), 1)
        r = self.client.get(f'/tasks/{t.id}/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['title'], 'A')

    def test_detail_404(self):
        r = self.client.get('/tasks/999/')
        self.assertEqual(r.status_code, 404)
        self.assertIn('error', r.json())

    # --- POST ---
    def test_create_ok(self):
        r = self.post({'title': ' Новая ', 'priority': 'high',
                       'project': self.project.id, 'category': self.category.id})
        self.assertEqual(r.status_code, 201)
        body = r.json()
        self.assertEqual(body['title'], 'Новая')
        self.assertEqual(body['status'], 'todo')
        self.assertEqual(body['project'], self.project.id)
        self.assertEqual(Task.objects.count(), 1)

    def test_create_requires_title(self):
        for body in ({}, {'title': ''}, {'title': '   '}, {'title': 5}):
            r = self.post(body)
            self.assertEqual(r.status_code, 400, body)
            self.assertIn('title', r.json()['details'])
        self.assertEqual(Task.objects.count(), 0)

    def test_create_invalid_choices_and_fk(self):
        r = self.post({'title': 'x', 'status': 'oops', 'priority': 'urgent',
                       'project': 12345, 'category': 'a'})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(set(r.json()['details']), {'status', 'priority', 'project', 'category'})

    def test_create_bad_json(self):
        r = self.client.post('/tasks/', data='{bad', content_type='application/json', **self.h)
        self.assertEqual(r.status_code, 400)
        r = self.client.post('/tasks/', data='[1, 2]', content_type='application/json', **self.h)
        self.assertEqual(r.status_code, 400)

    # --- PUT / PATCH ---
    def test_put_replaces_resource(self):
        t = Task.objects.create(title='Old', description='d', status='done', priority='high')
        r = self.client.put(f'/tasks/{t.id}/', data={'title': 'New'},
                            content_type='application/json', **self.h)
        self.assertEqual(r.status_code, 200)
        t.refresh_from_db()
        self.assertEqual((t.title, t.description, t.status, t.priority),
                         ('New', '', 'todo', 'medium'))

    def test_put_requires_title(self):
        t = Task.objects.create(title='Old')
        r = self.client.put(f'/tasks/{t.id}/', data={'status': 'done'},
                            content_type='application/json', **self.h)
        self.assertEqual(r.status_code, 400)

    def test_put_404(self):
        r = self.client.put('/tasks/999/', data={'title': 'x'},
                            content_type='application/json', **self.h)
        self.assertEqual(r.status_code, 404)

    def test_patch_partial(self):
        t = Task.objects.create(title='Old', priority='high')
        r = self.client.patch(f'/tasks/{t.id}/', data={'status': 'done'},
                              content_type='application/json', **self.h)
        self.assertEqual(r.status_code, 200)
        t.refresh_from_db()
        self.assertEqual((t.title, t.status, t.priority), ('Old', 'done', 'high'))

    # --- DELETE ---
    def test_delete(self):
        t = Task.objects.create(title='A')
        r = self.client.delete(f'/tasks/{t.id}/', **self.h)
        self.assertEqual(r.status_code, 204)
        self.assertFalse(Task.objects.filter(id=t.id).exists())
        self.assertEqual(self.client.delete(f'/tasks/{t.id}/', **self.h).status_code, 404)

    def test_method_not_allowed(self):
        r = self.client.delete('/tasks/', **self.h)
        self.assertEqual(r.status_code, 405)

    def test_api_prefix_works(self):
        r = self.client.post('/api/tasks/', data=json.dumps({'title': 'x'}),
                             content_type='application/json', **self.h)
        self.assertEqual(r.status_code, 201)


class ModelRelationTests(TestCase):
    def test_relations(self):
        p = Project.objects.create(name='P')
        c = Category.objects.create(name='C')
        t = Task.objects.create(title='T', project=p, category=c)
        self.assertEqual(list(p.tasks.all()), [t])
        c.delete()
        t.refresh_from_db()
        self.assertIsNone(t.category)       # SET_NULL
        p.delete()
        self.assertFalse(Task.objects.filter(pk=t.pk).exists())  # CASCADE
