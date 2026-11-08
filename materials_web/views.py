"""Страницы списка материалов и отдельного материала."""

from django.http import HttpResponse
from django.shortcuts import render

from db.database import MAX_ID
from db.orm_queries import fetch_all, fetch_one
from homepage.parameters import date_parameter, quantity_parameter


def materials(request) -> HttpResponse:
    """List or search materials using parameterized SQL."""
    name = request.GET.get('q', '').strip()
    quantity = request.GET.get('quantity', '')
    error = ''
    rows = []
    try:
        minimum = quantity_parameter(quantity)
        if name or quantity:
            rows = fetch_all('materials_search',
                             (name, minimum))
        else:
            rows = fetch_all('materials_list')
    except ValueError as exception:
        error = str(exception)
    context = {'materials': rows, 'q': name, 'quantity': quantity,
               'error': error}
    return render(request, 'materials_web/material_list.html', context,
                  status=400 if error else 200)


def material_detail(request, material_id: int) -> HttpResponse:
    """Показать карточку материала или вернуть HTTP 404."""
    material = (fetch_one('material_detail', (material_id,))
                if material_id <= MAX_ID else None)
    if material is None:
        return render(
            request,
            'materials_web/material_not_found.html',
            status=404,
        )

    context = {
        'material': material,
        'total_cost': material.total_cost,
    }
    return render(request, 'materials_web/material_detail.html', context)


def available(request) -> HttpResponse:
    """Find current stock, optionally excluding expenses on a selected date."""
    selected_date = request.GET.get('date', '')
    quantity = request.GET.get('quantity', '')
    rows = []
    error = ''
    try:
        minimum = quantity_parameter(quantity)
        date_parameter(selected_date)
        if selected_date:
            rows = fetch_all('materials_without_expense',
                             (minimum, selected_date))
        else:
            rows = fetch_all('materials_in_stock', (minimum,))
    except ValueError as exception:
        error = str(exception)
    context = {'materials': rows, 'selected_date': selected_date,
               'quantity': quantity, 'error': error}
    return render(request, 'materials_web/available.html', context,
                  status=400 if error else 200)
