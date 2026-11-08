"""Regression tests for templates and pages backed by isolated SQLite data."""

import os
from html.parser import HTMLParser

import django
import pytest


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventory_web.settings')
django.setup()

from django.contrib.staticfiles import finders  # noqa: E402
from django.template.loader import get_template  # noqa: E402
from django.http import Http404  # noqa: E402
from django.test import Client, RequestFactory, override_settings  # noqa: E402
from django.urls import resolve, reverse  # noqa: E402

from homepage.views import page_not_found  # noqa: E402
from materials import Material  # noqa: E402
from operations import Operation  # noqa: E402
from db import database  # noqa: E402
from db.import_json import import_json  # noqa: E402
from storage import save_data  # noqa: E402
from django.core.management import call_command  # noqa: E402
from django.test.utils import setup_databases, teardown_databases  # noqa: E402


@pytest.fixture(scope='session', autouse=True)
def orm_database():
    config = setup_databases(verbosity=0, interactive=False)
    yield
    teardown_databases(config, verbosity=0)


@pytest.fixture
def store_web_data(tmp_path, monkeypatch):
    monkeypatch.setattr(database, 'DB_PATH', tmp_path / 'web.sqlite')

    def store(data):
        save_data(data, tmp_path / 'json')
        import_json(tmp_path / 'json', replace=True)
        call_command('import_pr7', source=str(database.DB_PATH), replace=True,
                     verbosity=0)

    return store


@pytest.fixture(autouse=True)
def web_data(store_web_data):
    material = Material(1, 'Краска', 100, 10, 'л', 'Отделка')
    operation = Operation(1, material, 'expense', 2, '2026-10-18')
    data = {'materials': [material], 'operations': [operation]}
    store_web_data(data)
    return data


def test_main_pages_are_available():
    client = Client()
    for url in ('/', '/materials/', '/operations/'):
        response = client.get(url)
        assert response.status_code == 200
        assert 'text/html' in response['Content-Type']
        assert 'bootstrap' in response.content.decode().lower()


def test_templates_named_urls_and_static_files_are_configured():
    assert reverse('homepage:index') == '/'
    assert reverse('materials_web:materials') == '/materials/'
    material_url = reverse('materials_web:material_detail', args=[1])
    assert material_url == '/materials/1/'
    assert reverse('operations_web:operations') == '/operations/'
    assert reverse(
        'operations_web:operation_detail', args=[1],
    ) == '/operations/1/'

    for template_name in (
        'base.html',
        'includes/navigation.html',
        'homepage/index.html',
        'materials_web/material_list.html',
        'materials_web/material_detail.html',
        'operations_web/operation_list.html',
        'operations_web/operation_detail.html',
    ):
        assert get_template(template_name)

    for static_path in (
        'homepage/css/style.css',
        'homepage/js/main.js',
        'homepage/img/logo.svg',
    ):
        assert finders.find(static_path)


def test_base_template_connects_project_static_files():
    content = Client().get('/').content.decode()
    assert '/static/homepage/css/style.css' in content
    assert '/static/homepage/js/main.js' in content
    assert '/static/homepage/img/logo.svg' in content
    assert 'id="current-year"' in content


def test_material_detail_and_missing_material(web_data):
    client = Client()
    response = client.get('/materials/1/')
    assert response.status_code == 200
    assert 'Краска' in response.content.decode()

    response = client.get('/materials/999/')
    assert response.status_code == 404
    assert 'Материал не найден' in response.content.decode()


def test_operation_detail_and_missing_operation(web_data):
    client = Client()
    response = client.get('/operations/1/')
    assert response.status_code == 200
    assert 'Расход' in response.content.decode()

    response = client.get('/operations/999/')
    assert response.status_code == 404
    assert 'Операция не найдена' in response.content.decode()


@pytest.mark.parametrize('quantity, expected', [
    (0.001, '0,001'),
    (0.00001, '0,00001'),
    (1.23456789, '1,23456789'),
])
def test_web_quantities_preserve_fractional_precision(
    store_web_data, quantity, expected,
):
    material = Material(1, 'Краска', 100, quantity, 'кг', 'Отделка')
    operation = Operation(1, material, 'receipt', quantity, '2026-10-16')
    data = {'materials': [material], 'operations': [operation]}
    store_web_data(data)

    client = Client()
    for url in (
        '/materials/', '/materials/1/', '/operations/', '/operations/1/',
    ):
        response = client.get(url)
        assert response.status_code == 200
        assert expected in response.content.decode(), url


@pytest.mark.parametrize('url', [
    '/nonexistent/', '/materials/abc/', '/operations/abc/',
])
@override_settings(DEBUG=False)
def test_unknown_routes_use_custom_404(url):
    response = Client().get(url)
    content = response.content.decode()
    assert response.status_code == 404
    assert '404 - страница не найдена' in content
    assert 'На главную' in content
    assert 'bootstrap' in content
    assert 'URL patterns' not in content


def test_custom_404_does_not_expose_exception():
    response = page_not_found(
        RequestFactory().get('/nonexistent/'),
        Http404('<script>secret</script>'),
    )
    assert response.status_code == 404
    assert 'secret' not in response.content.decode()


@override_settings(DEBUG=False)
def test_http404_from_view_uses_global_handler(web_data, monkeypatch):
    def missing(*args):
        raise Http404('private lookup details')

    monkeypatch.setattr('materials_web.views.fetch_one', missing)
    response = Client().get('/materials/1/')
    content = response.content.decode()
    assert response.status_code == 404
    assert '404 - страница не найдена' in content
    assert 'private lookup details' not in content


@pytest.mark.parametrize('debug', [False, True])
@pytest.mark.parametrize('url, message', [
    ('/materials/999/', 'Материал не найден'),
    ('/operations/999/', 'Операция не найдена'),
])
def test_missing_objects_keep_specific_404(web_data, debug, url, message):
    with override_settings(DEBUG=debug):
        response = Client().get(url)
    assert response.status_code == 404
    assert message in response.content.decode()


@pytest.mark.parametrize('url, message', [
    ('/materials/', 'Материалы не найдены.'),
    ('/operations/', 'Операций пока нет.'),
])
def test_empty_lists(web_data, store_web_data, url, message):
    web_data['materials'].clear()
    web_data['operations'].clear()
    store_web_data(web_data)
    response = Client().get(url)
    assert response.status_code == 200
    assert message in response.content.decode()


def test_objects_and_text_are_displayed_safely(web_data, store_web_data):
    material = web_data['materials'][0]
    material.name = '<b>Краска</b>'
    material.quantity = 0
    operation = web_data['operations'][0]
    operation.cancelled = True
    operation.note = '<script>alert(1)</script>'
    store_web_data(web_data)
    client = Client()
    for url in ('/materials/', '/materials/1/'):
        content = client.get(url).content.decode()
        assert '&lt;b&gt;Краска&lt;/b&gt;' in content
        assert '<b>Краска</b>' not in content
        assert 'закончился' in content
    for url in ('/operations/', '/operations/1/'):
        content = client.get(url).content.decode()
        assert 'отменена' in content
        assert '<script>alert(1)</script>' not in content
    assert '&lt;script&gt;' in client.get('/operations/1/').content.decode()


def test_named_routes_and_navigation(web_data):
    class Links(HTMLParser):
        def __init__(self):
            super().__init__()
            self.hrefs = set()

        def handle_starttag(self, tag, attrs):
            if tag == 'a':
                self.hrefs.update(value for key, value in attrs
                                  if key == 'href' and value.startswith('/'))

    routes = [
        ('homepage:index', [], '/', 'homepage:index'),
        ('materials_web:materials', [], '/materials/',
         'materials_web:materials'),
        ('materials_web:material_detail', [1], '/materials/1/',
         'materials_web:material_detail'),
        ('operations_web:operations', [], '/operations/',
         'operations_web:operations'),
        ('operations_web:operation_detail', [1], '/operations/1/',
         'operations_web:operation_detail'),
    ]
    client = Client()
    for name, args, url, view_name in routes:
        assert reverse(name, args=args) == url
        assert resolve(url).view_name == view_name
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert '<!DOCTYPE html>' in content
        assert '<html lang="ru">' in content
        assert '<meta charset="UTF-8">' in content
        parser = Links()
        parser.feed(content)
        assert {'/', '/materials/', '/operations/'} <= parser.hrefs
        for href in parser.hrefs:
            assert client.get(href).status_code == 200


def test_sql_search_pages_and_statistics(web_data, store_web_data):
    paint = web_data['materials'][0]
    brush = Material(2, 'Кисть', 50, 3, 'шт', 'Инструменты')
    web_data['materials'].append(brush)
    web_data['operations'].append(
        Operation(2, brush, 'expense', 1, '2026-10-18', '', True),
    )
    store_web_data(web_data)
    client = Client()
    response = client.get('/materials/', {'q': paint.name, 'quantity': '4'})
    assert response.status_code == 200
    assert 'Краска' in response.content.decode()
    assert 'Кисть' not in response.content.decode()
    response = client.get('/materials/available/',
                          {'date': '2026-10-18', 'quantity': '1'})
    assert response.status_code == 200
    assert 'Кисть' in response.content.decode()
    assert 'Краска' not in response.content.decode()
    response = client.get('/operations/', {'state': 'active'})
    assert 'Краска' in response.content.decode()
    assert 'Кисть' not in response.content.decode()
    response = client.get('/operations/', {
        'state': 'cancelled', 'kind': 'expense', 'date': '2026-10-18',
    })
    assert 'Кисть' in response.content.decode()
    assert 'Краска' not in response.content.decode()
    assert 'Отменённые' in response.content.decode()
    response = client.get('/statistics/', {'threshold': '0'})
    assert response.status_code == 200
    assert 'Отделка' in response.content.decode()
    assert 'Инструменты' in response.content.decode()
    assert 'Нет операций' in response.content.decode()
    response = client.get('/statistics/', {'threshold': '5'})
    assert 'Нет материалов с такой активностью.' in response.content.decode()


@pytest.mark.parametrize('url, parameters', [
    ('/materials/', {'quantity': '-1'}),
    ('/materials/', {'quantity': 'abc'}),
    ('/materials/', {'quantity': 'nan'}),
    ('/materials/', {'quantity': '1e9999'}),
    ('/materials/available/', {'date': '2026-02-30'}),
    ('/materials/available/', {'date': '20261018'}),
    ('/materials/available/', {'quantity': '-5'}),
    ('/operations/', {'kind': 'unknown'}),
    ('/operations/', {'state': 'unknown'}),
    ('/operations/', {'date': 'not a date'}),
    ('/statistics/', {'threshold': '-1'}),
    ('/statistics/', {'threshold': 'abc'}),
    ('/statistics/', {'threshold': '99999999999999999999999'}),
])
def test_invalid_search_parameters_are_not_server_errors(url, parameters):
    response = Client().get(url, parameters)
    assert response.status_code == 400
    assert 'role="alert"' in response.content.decode()


def test_search_handles_empty_results_and_literal_wildcards():
    client = Client()
    for parameters in ({'q': 'missing'}, {'q': '%'}, {'q': '_'},
                       {'q': "' OR 1=1 --"}, {'quantity': '1000000'}):
        response = client.get('/materials/', parameters)
        assert response.status_code == 200
        assert 'Материалы не найдены.' in response.content.decode()


def test_pages_read_sqlite_not_json(monkeypatch):
    def reject(*args, **kwargs):
        raise AssertionError('Web requests must not load JSON')

    monkeypatch.setattr('storage.load_data', reject)
    for url in ('/', '/materials/', '/materials/1/', '/operations/',
                '/operations/1/', '/materials/available/', '/statistics/'):
        assert Client().get(url).status_code == 200


def test_all_queries_are_used_by_web_pages(monkeypatch):
    from db import orm_queries as queries

    used = set()
    for module in ('homepage.views', 'materials_web.views',
                   'operations_web.views'):
        for method in ('fetch_one', 'fetch_all'):
            original = getattr(queries, method)

            def record(name, parameters=(), original=original):
                used.add(name)
                return original(name, parameters)

            monkeypatch.setattr(f'{module}.{method}', record)
    for url in ('/', '/materials/', '/materials/?q=Краска',
                '/materials/1/', '/materials/available/',
                '/materials/available/?date=2026-10-18',
                '/operations/', '/operations/?state=active',
                '/operations/?kind=expense', '/operations/1/', '/statistics/'):
        assert Client().get(url).status_code == 200
    assert len(used) == 16


@pytest.mark.parametrize('section', ['materials', 'operations'])
def test_ids_outside_sqlite_integer_range_are_not_server_errors(section):
    response = Client().get(f'/{section}/{2 ** 80}/')
    assert response.status_code == 404


def test_new_pages_support_empty_database(web_data, store_web_data):
    web_data['operations'].clear()
    web_data['materials'].clear()
    store_web_data(web_data)
    for url in ('/', '/statistics/', '/materials/available/'):
        assert Client().get(url).status_code == 200


def test_orm_crud_and_protected_relationship():
    from django.db.models.deletion import ProtectedError
    from materials_web.models import Material as Stock
    from operations_web.models import Operation as Movement
    from operations_web.services import record_operation, cancel_operation

    material = Stock.objects.create(name='Test', price=1, quantity=5,
                                    unit='kg', category='Test')
    operation = record_operation(material.pk, 'expense', 2, '2026-11-08')
    material.refresh_from_db()
    assert material.quantity == 3
    assert material.operations.get().pk == operation.pk
    with pytest.raises(ProtectedError):
        material.delete()
    with pytest.raises(ValueError):
        record_operation(material.pk, 'expense', 99, '2026-11-08')
    assert Movement.objects.filter(material=material).count() == 1
    cancel_operation(operation.pk)
    material.refresh_from_db()
    assert material.quantity == 5
    with pytest.raises(ValueError):
        cancel_operation(operation.pk)
    operation.delete()
    material.name = 'Updated'
    material.save()
    assert Stock.objects.get(pk=material.pk).name == 'Updated'
    material.delete()
    assert not Stock.objects.filter(pk=material.pk).exists()


def test_pagination_retains_filters_and_order():
    from operations_web.models import Operation as Movement

    Movement.objects.bulk_create([
        Movement(material_id=1, kind='expense', quantity=1,
                 date='2026-11-08', note=f'Pagination {i}')
        for i in range(23)
    ])
    response = Client().get('/operations/', {
        'q': 'Pagination', 'state': 'active', 'sort': 'oldest', 'page': 2,
    })
    content = response.content.decode()
    assert response.status_code == 200
    assert '2 / 3' in content
    assert 'q=Pagination' in content and 'sort=oldest' in content
    assert 'state=active' in content and 'page=3' in content
    assert Client().get('/operations/?sort=unknown').status_code == 400


def test_web_never_opens_legacy_sqlite(monkeypatch):
    def reject(*args, **kwargs):
        raise AssertionError('Legacy SQL access in HTTP request')

    monkeypatch.setattr(database, 'get_connection', reject)
    for url in ('/', '/materials/', '/operations/', '/statistics/'):
        assert Client().get(url).status_code == 200
