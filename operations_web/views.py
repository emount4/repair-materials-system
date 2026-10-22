"""Страницы списка операций и отдельной операции."""

from django.http import HttpResponse
from django.shortcuts import render

from db.database import MAX_ID
from db.queries import fetch_all, fetch_one
from homepage.parameters import date_parameter


def operations(request) -> HttpResponse:
    """Filter the movement journal by state, date and kind in SQL."""
    kind = request.GET.get('kind', '')
    selected_date = request.GET.get('date', '')
    state = request.GET.get('state', '')
    error = ''
    rows = []
    try:
        if kind not in ('', 'receipt', 'expense'):
            raise ValueError('Неизвестный вид операции.')
        if state not in ('', 'active', 'cancelled'):
            raise ValueError('Неизвестный статус операции.')
        date_parameter(selected_date)
        if state == 'active' and not kind and not selected_date:
            rows = fetch_all('active_operations')
        elif not any((kind, selected_date, state)):
            rows = fetch_all('operations_list')
        else:
            cancelled = {'': '', 'active': 0, 'cancelled': 1}[state]
            parameters = (kind, kind, selected_date, selected_date,
                          cancelled, cancelled)
            rows = fetch_all('operations_filter', parameters)
    except ValueError as exception:
        error = str(exception)
    context = {'operations': rows, 'kind': kind, 'state': state,
               'selected_date': selected_date, 'error': error}
    return render(request, 'operations_web/operation_list.html', context,
                  status=400 if error else 200)


def operation_detail(request, operation_id: int) -> HttpResponse:
    """Показать карточку операции или вернуть HTTP 404."""
    operation = (fetch_one('operation_detail', (operation_id,))
                 if operation_id <= MAX_ID else None)
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
