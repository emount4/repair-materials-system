"""Страницы списка материалов и отдельного материала."""

from django.http import HttpResponse
from django.shortcuts import render

from materials import find_material_by_id
from storage import load_data


def materials(request) -> HttpResponse:
    """Показать материалы из JSON-хранилища."""
    context = {'materials': load_data()['materials']}
    return render(request, 'materials_web/material_list.html', context)


def material_detail(request, material_id: int) -> HttpResponse:
    """Показать карточку материала или вернуть HTTP 404."""
    materials_list = load_data()['materials']
    material = find_material_by_id(materials_list, material_id)
    if material is None:
        return render(
            request,
            'materials_web/material_not_found.html',
            status=404,
        )

    context = {
        'material': material,
        'total_cost': material.calculate_cost(material.quantity),
    }
    return render(request, 'materials_web/material_detail.html', context)
