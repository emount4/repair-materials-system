"""Проверки Django-маршрутов и веб-страниц ПР5."""

import os

import django


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventory_web.settings')
django.setup()

from django.test import Client  # noqa: E402


def test_main_pages_are_available():
    client = Client()
    for url in ('/', '/materials/', '/operations/'):
        response = client.get(url)
        assert response.status_code == 200
        assert 'text/html' in response['Content-Type']
        assert 'bootstrap' in response.content.decode().lower()


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
