"""Страницы списка операций и отдельной операции."""

from django.http import HttpResponse
from django.shortcuts import render

from storage import load_data


def operations(request) -> HttpResponse:
    """Показать историю операций из JSON-хранилища."""
    context = {'operations': load_data()['operations']}
    return render(request, 'operations_web/operation_list.html', context)


def operation_detail(request, operation_id: int) -> HttpResponse:
    """Показать карточку операции или вернуть HTTP 404."""
    operation = next(
        (
            item for item in load_data()['operations']
            if item.id == operation_id
        ),
        None,
    )
    if operation is None:
        return render(
            request,
            'operations_web/operation_not_found.html',
            status=404,
        )

    return render(
        request,
        'operations_web/operation_detail.html',
        {'operation': operation},
    )
