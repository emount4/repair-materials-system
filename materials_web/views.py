"""Страницы списка материалов и отдельного материала."""

from html import escape

from django.http import HttpResponse

from homepage.views import page
from materials import find_material_by_id
from storage import load_data


def _number(value: float) -> str:
    """Показать число без лишнего десятичного нуля."""
    return f'{value:g}'


def materials(request) -> HttpResponse:
    """Показать материалы из JSON-хранилища."""
    materials_list = load_data()['materials']
    rows = []
    for material in materials_list:
        availability = (
            '<span class="badge text-bg-success">в наличии</span>'
            if material.quantity > 0
            else '<span class="badge text-bg-danger">закончился</span>'
        )
        rows.append(f"""
<tr>
    <td class="text-secondary">#{material.id}</td>
    <td>
        <a class="fw-semibold link-dark" href="/materials/{material.id}/">
            {escape(material.name)}
        </a>
    </td>
    <td>{escape(material.category)}</td>
    <td>{_number(material.quantity)} {escape(material.unit)}</td>
    <td>{material.price:.2f} руб.</td>
    <td>{availability}</td>
</tr>""")
    body = ''.join(rows) or (
        '<tr><td colspan="6" class="text-center py-4">'
        'Материалы не найдены.</td></tr>'
    )
    content = f"""
<div class="d-flex justify-content-between align-items-end mb-3">
    <div>
        <p class="text-success fw-semibold mb-1">Склад</p>
        <h1 class="h2 mb-0">Материалы</h1>
    </div>
    <span class="badge text-bg-dark">Позиций: {len(materials_list)}</span>
</div>
<div class="table-responsive bg-white shadow-sm">
    <table class="table table-hover mb-0">
        <thead class="table-light">
            <tr>
                <th>ID</th><th>Название</th><th>Категория</th>
                <th>Остаток</th><th>Цена</th><th>Статус</th>
            </tr>
        </thead>
        <tbody>{body}</tbody>
    </table>
</div>
"""
    return HttpResponse(page('Материалы', content))


def material_detail(request, material_id: int) -> HttpResponse:
    """Показать карточку материала или вернуть HTTP 404."""
    materials_list = load_data()['materials']
    material = find_material_by_id(materials_list, material_id)
    if material is None:
        content = """
<h1 class="h2 text-danger">Материал не найден</h1>
<p>Позиции с указанным идентификатором нет в JSON-хранилище.</p>
<a class="btn btn-outline-dark" href="/materials/">
    <i class="bi bi-arrow-left me-2"></i>К списку материалов
</a>
"""
        return HttpResponse(
            page('Материал не найден', content),
            status=404,
        )

    stock_status = 'в наличии' if material.quantity > 0 else 'закончился'
    badge = 'text-bg-success' if material.quantity > 0 else 'text-bg-danger'
    total_cost = material.calculate_cost(material.quantity)
    content = f"""
<p class="text-success fw-semibold mb-1">Карточка материала</p>
<h1 class="h2 mb-3">{escape(material.name)}</h1>
<article class="card border-0 shadow-sm mb-3">
    <div class="card-body">
        <div class="d-flex justify-content-between gap-3 mb-3">
            <span class="text-secondary">Материал #{material.id}</span>
            <span class="badge {badge}">{stock_status}</span>
        </div>
        <dl class="row mb-0">
            <dt class="col-sm-4">Категория</dt>
            <dd class="col-sm-8">{escape(material.category)}</dd>
            <dt class="col-sm-4">Цена за единицу</dt>
            <dd class="col-sm-8">{material.price:.2f} руб.</dd>
            <dt class="col-sm-4">Остаток</dt>
            <dd class="col-sm-8">
                {_number(material.quantity)} {escape(material.unit)}
            </dd>
            <dt class="col-sm-4">Стоимость остатка</dt>
            <dd class="col-sm-8">{total_cost:.2f} руб.</dd>
        </dl>
    </div>
</article>
<a class="btn btn-outline-dark" href="/materials/">
    <i class="bi bi-arrow-left me-2"></i>К списку материалов
</a>
"""
    return HttpResponse(page(material.name, content))
