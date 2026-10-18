"""Проверки Django-маршрутов, шаблонов и веб-страниц ПР6."""

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


@pytest.fixture
def web_data(monkeypatch):
    material = Material(1, 'Краска', 100, 10, 'л', 'Отделка')
    operation = Operation(1, material, 'expense', 2, '2026-10-18')
    data = {'materials': [material], 'operations': [operation]}
    for module in ('homepage.views', 'materials_web.views',
                   'operations_web.views'):
        monkeypatch.setattr(f'{module}.load_data', lambda: data)
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
    monkeypatch, quantity, expected,
):
    material = Material(1, 'Краска', 100, quantity, 'кг', 'Отделка')
    operation = Operation(1, material, 'receipt', quantity, '2026-10-16')
    data = {'materials': [material], 'operations': [operation]}
    for module in ('materials_web.views', 'operations_web.views'):
        monkeypatch.setattr(f'{module}.load_data', lambda: data)

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

    monkeypatch.setattr('materials_web.views.find_material_by_id', missing)
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
def test_empty_lists(web_data, url, message):
    web_data['materials'].clear()
    web_data['operations'].clear()
    response = Client().get(url)
    assert response.status_code == 200
    assert message in response.content.decode()


def test_objects_and_text_are_displayed_safely(web_data):
    material = web_data['materials'][0]
    material.name = '<b>Краска</b>'
    material.quantity = 0
    operation = web_data['operations'][0]
    operation.cancelled = True
    operation.note = '<script>alert(1)</script>'
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
