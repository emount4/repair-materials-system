"""Главная страница проекта."""

from django.http import HttpResponse
from django.shortcuts import render

from materials import get_statistics
from storage import load_data


def page_not_found(request, exception) -> HttpResponse:
    """Показать общую страницу 404 через Django-шаблон."""
    return render(request, 'homepage/page_not_found.html', status=404)


def index(request) -> HttpResponse:
    """Показать назначение проекта, статистику и основные разделы."""
    data = load_data()
    context = {
        'statistics': get_statistics(data['materials']),
        'operations_count': len(data['operations']),
    }
    return render(request, 'homepage/index.html', context)
