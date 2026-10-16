"""Проверки Django-маршрутов, шаблонов и веб-страниц ПР6."""

import os

import django
import pytest


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventory_web.settings')
django.setup()

from django.contrib.staticfiles import finders  # noqa: E402
from django.template.loader import get_template  # noqa: E402
from django.test import Client  # noqa: E402
from django.urls import reverse  # noqa: E402

from materials import Material  # noqa: E402
from operations import Operation  # noqa: E402


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


def test_material_detail_and_missing_material():
    client = Client()
    response = client.get('/materials/1/')
    assert response.status_code == 200
    assert 'jhdsh' in response.content.decode()

    response = client.get('/materials/999/')
    assert response.status_code == 404
    assert 'Материал не найден' in response.content.decode()


def test_operation_detail_and_missing_operation():
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
