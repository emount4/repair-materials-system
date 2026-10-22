"""Главная страница проекта."""

from django.http import HttpResponse
from django.shortcuts import render

from db.queries import fetch_all, fetch_one


def page_not_found(request, exception) -> HttpResponse:
    """Показать общую страницу 404 через Django-шаблон."""
    return render(request, 'homepage/page_not_found.html', status=404)


def index(request) -> HttpResponse:
    """Показать назначение проекта, статистику и основные разделы."""
    context = {
        'statistics': fetch_one('stock_summary'),
        'operations_count': fetch_one('operation_summary')['operations_count'],
    }
    return render(request, 'homepage/index.html', context)


def statistics(request) -> HttpResponse:
    """Show SQL aggregates, grouped stock and material movement statistics."""
    threshold = request.GET.get('threshold', '0')
    error = ''
    try:
        minimum = int(threshold)
        if not 0 <= minimum <= 1_000_000_000:
            raise ValueError
    except ValueError:
        minimum = 0
        error = 'Порог должен быть целым числом от 0 до 1000000000.'
    context = {
        'statistics': fetch_one('stock_summary'),
        'summary': fetch_one('operation_summary'),
        'categories': fetch_all('category_statistics'),
        'activity': fetch_all('material_activity'),
        'frequent': fetch_all('frequent_materials', (minimum,)),
        'threshold': threshold,
        'error': error,
    }
    return render(request, 'homepage/statistics.html', context,
                  status=400 if error else 200)
