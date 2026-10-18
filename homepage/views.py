"""Общий каркас страниц и главная страница проекта."""

from html import escape

from django.http import HttpResponse

from materials import get_statistics
from storage import load_data


def page(title: str, content: str) -> str:
    """Собрать единый HTML-каркас с Bootstrap и навигацией."""
    bootstrap = (
        'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/'
        'dist/css/bootstrap.min.css'
    )
    icons = (
        'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/'
        'font/bootstrap-icons.min.css'
    )
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{escape(title)}</title>
    <link rel="icon" href="data:,">
    <link rel="stylesheet" href="{bootstrap}">
    <link rel="stylesheet" href="{icons}">
    <style>
        body {{ background: #f4f6f8; color: #20252b; }}
        .navbar {{ border-bottom: 3px solid #2b7a4b; }}
        .brand-mark {{ color: #f0b429; }}
        .page-shell {{ max-width: 1040px; }}
        .metric {{ border-left: 4px solid #2b7a4b; }}
        .table > :not(caption) > * > * {{ vertical-align: middle; }}
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg bg-dark" data-bs-theme="dark">
        <div class="container page-shell">
            <a class="navbar-brand fw-semibold" href="/">
                <i class="bi bi-box-seam brand-mark me-2"></i>Материалы ИП
            </a>
            <div class="navbar-nav flex-row gap-2 gap-md-3">
                <a class="nav-link" href="/">Главная</a>
                <a class="nav-link" href="/materials/">Материалы</a>
                <a class="nav-link" href="/operations/">Операции</a>
            </div>
        </div>
    </nav>
    <main class="container page-shell py-4 py-md-5">{content}</main>
</body>
</html>"""


def page_not_found(request, exception) -> HttpResponse:
    """Показать общую страницу 404 для неизвестного адреса или Http404."""
    content = """
<h1 class="h2 text-danger">404 - страница не найдена</h1>
<p>Проверьте адрес или вернитесь на главную.</p>
<a class="btn btn-outline-dark" href="/">На главную</a>
"""
    return HttpResponse(page('404 - страница не найдена', content), status=404)


def index(request) -> HttpResponse:
    """Показать назначение проекта, статистику и основные разделы."""
    data = load_data()
    statistics = get_statistics(data['materials'])
    content = f"""
<section class="mb-4">
    <p class="text-uppercase text-success fw-semibold mb-2">
        Складской учет для ремонтных работ
    </p>
    <h1 class="display-5 fw-bold">Система учета материалов ИП</h1>
    <p class="lead col-lg-9">
        Веб-интерфейс показывает текущие остатки материалов и историю
        поступлений и расходов из JSON-файлов индивидуального проекта.
    </p>
</section>
<section class="row g-3 mb-4" aria-label="Сводка">
    <div class="col-sm-6 col-lg-3">
        <div class="metric bg-white p-3 h-100 shadow-sm">
            <div class="text-secondary small">Материалов</div>
            <div class="fs-3 fw-bold">{statistics['count']}</div>
        </div>
    </div>
    <div class="col-sm-6 col-lg-3">
        <div class="metric bg-white p-3 h-100 shadow-sm">
            <div class="text-secondary small">Категорий</div>
            <div class="fs-3 fw-bold">{statistics['categories']}</div>
        </div>
    </div>
    <div class="col-sm-6 col-lg-3">
        <div class="metric bg-white p-3 h-100 shadow-sm">
            <div class="text-secondary small">Нет в наличии</div>
            <div class="fs-3 fw-bold">{statistics['out_of_stock']}</div>
        </div>
    </div>
    <div class="col-sm-6 col-lg-3">
        <div class="metric bg-white p-3 h-100 shadow-sm">
            <div class="text-secondary small">Стоимость запасов</div>
            <div class="fs-5 fw-bold">
                {statistics['total_cost']:.2f} руб.
            </div>
        </div>
    </div>
</section>
<section class="d-flex flex-wrap gap-2">
    <a class="btn btn-success" href="/materials/">
        <i class="bi bi-boxes me-2"></i>Открыть материалы
    </a>
    <a class="btn btn-outline-dark" href="/operations/">
        <i class="bi bi-arrow-left-right me-2"></i>Открыть операции
    </a>
</section>
"""
    return HttpResponse(page('Учет материалов ИП', content))
