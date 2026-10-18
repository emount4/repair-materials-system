"""Страницы списка операций и отдельной операции."""

from html import escape

from django.http import HttpResponse

from homepage.views import page
from operations import find_operation_by_id
from storage import load_data


def _kind(operation) -> str:
    return 'Поступление' if operation.kind == 'receipt' else 'Расход'


def _status(operation) -> tuple[str, str]:
    if operation.cancelled:
        return 'отменена', 'text-bg-secondary'
    return 'действует', 'text-bg-success'


def operations(request) -> HttpResponse:
    """Показать историю операций из JSON-хранилища."""
    operations_list = load_data()['operations']
    rows = []
    for operation in operations_list:
        status, badge = _status(operation)
        rows.append(f"""
<tr>
    <td class="text-secondary">#{operation.id}</td>
    <td>
        <a class="fw-semibold link-dark" href="/operations/{operation.id}/">
            {_kind(operation)}
        </a>
    </td>
    <td>
        <a href="/materials/{operation.material.id}/">
            {escape(operation.material.name)}
        </a>
    </td>
    <td>{operation.quantity:g} {escape(operation.material.unit)}</td>
    <td>{escape(operation.date)}</td>
    <td><span class="badge {badge}">{status}</span></td>
</tr>""")
    body = ''.join(rows) or (
        '<tr><td colspan="6" class="text-center py-4">'
        'Операций пока нет.</td></tr>'
    )
    content = f"""
<div class="d-flex justify-content-between align-items-end mb-3">
    <div>
        <p class="text-success fw-semibold mb-1">Журнал движения</p>
        <h1 class="h2 mb-0">Операции</h1>
    </div>
    <span class="badge text-bg-dark">Записей: {len(operations_list)}</span>
</div>
<div class="table-responsive bg-white shadow-sm">
    <table class="table table-hover mb-0">
        <thead class="table-light">
            <tr>
                <th>ID</th><th>Вид</th><th>Материал</th>
                <th>Количество</th><th>Дата</th><th>Статус</th>
            </tr>
        </thead>
        <tbody>{body}</tbody>
    </table>
</div>
"""
    return HttpResponse(page('Операции', content))


def operation_detail(request, operation_id: int) -> HttpResponse:
    """Показать карточку операции или вернуть HTTP 404."""
    operations_list = load_data()['operations']
    operation = find_operation_by_id(operations_list, operation_id)
    if operation is None:
        content = """
<h1 class="h2 text-danger">Операция не найдена</h1>
<p>Записи с указанным идентификатором нет в JSON-хранилище.</p>
<a class="btn btn-outline-dark" href="/operations/">
    <i class="bi bi-arrow-left me-2"></i>К истории операций
</a>
"""
        return HttpResponse(
            page('Операция не найдена', content),
            status=404,
        )

    status, badge = _status(operation)
    note = escape(operation.note) if operation.note else 'Без примечания'
    content = f"""
<p class="text-success fw-semibold mb-1">Карточка операции</p>
<h1 class="h2 mb-3">{_kind(operation)} #{operation.id}</h1>
<article class="card border-0 shadow-sm mb-3">
    <div class="card-body">
        <div class="d-flex justify-content-between gap-3 mb-3">
            <span class="text-secondary">{escape(operation.date)}</span>
            <span class="badge {badge}">{status}</span>
        </div>
        <dl class="row mb-0">
            <dt class="col-sm-4">Материал</dt>
            <dd class="col-sm-8">
                <a href="/materials/{operation.material.id}/">
                    {escape(operation.material.name)}
                </a>
            </dd>
            <dt class="col-sm-4">Количество</dt>
            <dd class="col-sm-8">
                {operation.quantity:g} {escape(operation.material.unit)}
            </dd>
            <dt class="col-sm-4">Примечание</dt>
            <dd class="col-sm-8">{note}</dd>
        </dl>
    </div>
</article>
<a class="btn btn-outline-dark" href="/operations/">
    <i class="bi bi-arrow-left me-2"></i>К истории операций
</a>
"""
    title = f'{_kind(operation)} #{operation.id}'
    return HttpResponse(page(title, content))
